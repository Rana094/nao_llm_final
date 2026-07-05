import os
import socket
import subprocess
import uuid
from pathlib import Path

import librosa
import numpy as np
import torch
from flask import Flask, jsonify, redirect, render_template, request
from rapidfuzz import fuzz
from transformers import AutoModelForSpeechSeq2Seq, AutoModelForSeq2SeqLM, AutoTokenizer
from werkzeug.utils import secure_filename
from bangla_audio import (
    detect_yes_no,
    needs_confirmation,
    get_confirm_command,
    get_do_command,
    get_cancel_command,
)

# ------------------------------------------------------------
# Basic configuration
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

ASR_MODEL_PATH = BASE_DIR / "models" / "moonshine-base-bn"
NLLB_MODEL_PATH = BASE_DIR / "models" / "nllb-200-distilled-600M"

PYTHON2 = "/home/rana/.pyenv/versions/2.7.18/bin/python"
NAO_SCRIPT = str(BASE_DIR / "nao_control.py")
NAOQI_PATH = "/home/rana/nao-sdk/pynaoqi/lib/python2.7/site-packages"
# NAO_IP = os.environ.get("NAO_IP", "10.34.4.28")
NAO_IP = os.environ.get("NAO_IP", "192.168.10.138")
NAO_CAMERA_URL = os.environ.get("NAO_CAMERA_URL", "")

ALLOWED_EXTENSIONS = {".wav", ".ogg", ".mp3", ".m4a", ".webm"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# ------------------------------------------------------------
# Global model state
# ------------------------------------------------------------

asr_tokenizer = None
asr_model = None
nllb_tokenizer = None
nllb_model = None
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
ASR_DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32
NLLB_DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32
robot_connected = False
pending_command = None


def load_models():
    """Load the ASR and translation models once and reuse them."""
    global asr_tokenizer, asr_model, nllb_tokenizer, nllb_model

    if asr_model is not None and nllb_model is not None:
        return

    if not ASR_MODEL_PATH.exists():
        raise FileNotFoundError(f"Moonshine model folder not found: {ASR_MODEL_PATH}")
    if not NLLB_MODEL_PATH.exists():
        raise FileNotFoundError(f"NLLB model folder not found: {NLLB_MODEL_PATH}")

    print("Loading Moonshine ASR model...")
    asr_tokenizer = AutoTokenizer.from_pretrained(str(ASR_MODEL_PATH), local_files_only=True)
    asr_model = AutoModelForSpeechSeq2Seq.from_pretrained(
        str(ASR_MODEL_PATH),
        dtype=ASR_DTYPE,
        low_cpu_mem_usage=True,
        local_files_only=True,
    ).to(DEVICE)
    asr_model.eval()

    print("Loading NLLB translator...")
    nllb_tokenizer = AutoTokenizer.from_pretrained(str(NLLB_MODEL_PATH), local_files_only=True)
    nllb_model = AutoModelForSeq2SeqLM.from_pretrained(
        str(NLLB_MODEL_PATH),
        dtype=NLLB_DTYPE,
        local_files_only=True,
    ).to(DEVICE)
    nllb_model.eval()


def allowed_file(filename):
    """Keep upload validation simple and beginner-friendly."""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def transcribe_audio(audio_path):
    """Load audio, resample it to 16kHz, and run the local Moonshine ASR model."""
    load_models()

    audio, _ = librosa.load(str(audio_path), sr=16000, mono=True)

    if audio.size == 0:
        return ""

    # Make the sequence length divisible by 320 for the model pipeline.
    remainder = len(audio) % 320
    if remainder:
        audio = np.concatenate([audio, np.zeros(320 - remainder, dtype=np.float32)])

    input_values = torch.tensor(audio).unsqueeze(0).to(DEVICE, dtype=ASR_DTYPE)

    start_id = asr_tokenizer.cls_token_id or 2
    eos_id = asr_tokenizer.sep_token_id or 3
    pad_id = asr_tokenizer.pad_token_id or 0

    with torch.no_grad():
        generated_ids = asr_model.generate(
            input_values,
            max_new_tokens=80,
            num_beams=1,
            decoder_start_token_id=start_id,
            pad_token_id=pad_id,
            eos_token_id=eos_id,
        )

    bangla_text = asr_tokenizer.decode(generated_ids[0].tolist(), skip_special_tokens=True)
    return bangla_text.strip()


def translate_bangla_to_english(text):
    """Translate Bangla text to English using the local NLLB model."""
    if not text or not text.strip():
        return ""

    load_models()

    nllb_tokenizer.src_lang = "ben_Beng"
    inputs = nllb_tokenizer(text, return_tensors="pt").to(DEVICE)
    english_token_id = nllb_tokenizer.convert_tokens_to_ids("eng_Latn")

    with torch.no_grad():
        generated_ids = nllb_model.generate(
            **inputs,
            forced_bos_token_id=english_token_id,
            max_length=200,
            num_beams=1,
        )

    return nllb_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()


def check_nao_connection(timeout=0.5):
    """Check whether the NAO robot network port is reachable."""
    try:
        with socket.create_connection((NAO_IP, 9559), timeout=timeout):
            return True
    except Exception:
        return False


@app.route("/robot-status")
def robot_status():
    status = "connected" if check_nao_connection() else "disconnected"
    return jsonify({"status": status})


@app.route("/camera-feed")
def camera_feed():
    if not NAO_CAMERA_URL:
        return (
            "<html><body style=\"background:#07111f;color:#f5f7fb;" \
            "font-family:Arial,sans-serif;padding:24px;\">"
            "<h2>Camera stream not configured</h2>"
            "<p>Set the <code>NAO_CAMERA_URL</code> environment variable and restart the app.</p>"
            "</body></html>",
            404,
            {"Content-Type": "text/html"},
        )
    return redirect(NAO_CAMERA_URL)


def detect_command(text):
    """Match Bangla voice input to the supported NAO commands with RapidFuzz."""
    cleaned = (text or "").lower().strip()

    commands = {
        "sit": ["বস", "বসো", "বসুন", "sit", "bosho", "boso"],
        "stand": ["দাঁড়াও", "দাড়াও", "দাঁড়া", "উঠ", "উঠো", "stand"],
        "hello": ["হ্যালো", "হেলো", "সালাম", "hello", "hi", "hey"],
        "name": ["নাম", "তোমার নাম", "আপনার নাম", "name"],
        "walk_forward": ["সামনে যাও", "সামনে", "আগে যাও", "forward", "go forward"],
        "go_back": [
    "পিছনে যাও",
    "পেছনে যাও",
    "পিছনে যাও",
    "ব্যাক",
    "পিছনে",
    "go back",
    "backward",
    "move back"
],

"salute": [
    "স্যালুট",
    "স্যালুট দাও",
    "স্যালুট করো",
    "salute"
],
        "turn_left": ["বামে ঘুরো", "বাম দিকে", "left"],
        "turn_right": ["ডানে ঘুরো", "ডান দিকে", "right"],
        "right_hand": ["হাত নাড়াও", "ডান হাত", "right hand", "wave"],
        "left_hand": ["বাম হাত","বাম হাত নাড়াও","বাম হাত নাড়াও","left hand","wave left hand"],
        "rest": ["ঘুমাও", "রেস্ট", "rest", "sleep"],
    }

    for command, keywords in commands.items():
        for keyword in keywords:
            if keyword in cleaned:
                return command

    best_score = 0
    best_command = "unknown"

    for command, keywords in commands.items():
        for keyword in keywords:
            score = fuzz.partial_ratio(keyword.lower(), cleaned)
            if score > best_score:
                best_score = score
                best_command = command

    if best_score >= 80:
        return best_command

    return "unknown"


def send_to_nao(command):
    """Send the detected command to the Python 2.7 NAO bridge script."""
    global robot_connected

    if not os.path.exists(PYTHON2):
        robot_connected = False
        raise FileNotFoundError(f"Python 2.7 interpreter not found: {PYTHON2}")
    if not os.path.exists(NAO_SCRIPT):
        robot_connected = False
        raise FileNotFoundError(f"NAO control script not found: {NAO_SCRIPT}")

    env = os.environ.copy()
    env["PYTHONPATH"] = NAOQI_PATH

    result = subprocess.run(
        [PYTHON2, NAO_SCRIPT, command],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        robot_connected = False
        raise RuntimeError(result.stderr or result.stdout or "Robot command failed")

    robot_connected = True
    return True


# ------------------------------------------------------------
# Flask routes
# ------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process-audio", methods=["POST"])
def process_audio():
    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file was received."}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"success": False, "error": "Empty filename."}), 400

    if not allowed_file(audio_file.filename):
        return jsonify({"success": False, "error": "Only audio files are allowed."}), 400

    # Simple size guard to protect the server.
    audio_file.stream.seek(0, os.SEEK_END)
    file_size = audio_file.stream.tell()
    audio_file.stream.seek(0)
    if file_size > MAX_CONTENT_LENGTH:
        return jsonify({"success": False, "error": "File is too large."}), 413

    filename = secure_filename(audio_file.filename)
    safe_name = f"{uuid.uuid4().hex}_{filename}"
    save_path = UPLOAD_FOLDER / safe_name

    try:
        audio_file.save(save_path)
        bangla_text = transcribe_audio(save_path)
        english_text = translate_bangla_to_english(bangla_text)


        global pending_command

        command = detect_command(bangla_text)

        # If NAO is waiting for yes/no answer
        if pending_command is not None:
            answer = detect_yes_no(bangla_text)

            if answer == "yes":
                nao_command = get_do_command(pending_command)
                send_to_nao(nao_command)
                robot_status = "confirmed and executed"
                command = nao_command
                pending_command = None

            elif answer == "no":
                nao_command = get_cancel_command(pending_command)
                send_to_nao(nao_command)
                robot_status = "cancelled"
                command = nao_command
                pending_command = None

            else:
                send_to_nao("unknown")
                robot_status = "confirmation not understood"

        # Normal command detection
        else:
            if command == "unknown":
                send_to_nao("unknown")
                robot_status = "unknown command"

            elif needs_confirmation(command):
                pending_command = command
                confirm_command = get_confirm_command(command)
                send_to_nao(confirm_command)
                robot_status = "waiting for confirmation"

            else:
                send_to_nao(command)
                robot_status = "sent"

        return jsonify(
            {
                "success": True,
                "bangla": bangla_text,
                "english": english_text,
                "command": command,
                "robot_status": robot_status,
            }
        )
    except Exception as exc:
        app.logger.exception("Audio processing failed")
        return jsonify({"success": False, "error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting app on https://0.0.0.0:{port}")
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        ssl_context="adhoc"
    )
