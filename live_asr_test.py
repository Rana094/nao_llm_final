import os
from pathlib import Path
import tempfile
import subprocess

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
import librosa
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from transformers import AutoTokenizer, AutoModelForSpeechSeq2Seq, AutoModelForSeq2SeqLM
from rapidfuzz import fuzz


BASE_DIR = Path(__file__).resolve().parent

ASR_MODEL_PATH = BASE_DIR / "models" / "moonshine-base-bn"
NLLB_MODEL_PATH = BASE_DIR / "models" / "nllb-200-distilled-600M"

PYTHON2 = "/home/rana/.pyenv/versions/2.7.18/bin/python"
NAO_SCRIPT = "/home/rana/Projects/nao-project/nao_control.py"
NAOQI_PATH = "/home/rana/nao-sdk/pynaoqi/lib/python2.7/site-packages"

MIC_DEVICE = 7
RECORD_SAMPLE_RATE = 48000
ASR_SAMPLE_RATE = 16000
RECORD_SECONDS = 6

device = "cuda" if torch.cuda.is_available() else "cpu"
asr_dtype = torch.float16 if device == "cuda" else torch.float32
nllb_dtype = torch.float16 if device == "cuda" else torch.float32

print("Running fully offline")
print("Device:", device)

print("Loading Moonshine ASR model...")
asr_tokenizer = AutoTokenizer.from_pretrained(str(ASR_MODEL_PATH), local_files_only=True)

asr_model = AutoModelForSpeechSeq2Seq.from_pretrained(
    str(ASR_MODEL_PATH),
    dtype=asr_dtype,
    low_cpu_mem_usage=True,
    local_files_only=True
).to(device)

START_ID = asr_tokenizer.cls_token_id or 2
EOS_ID = asr_tokenizer.sep_token_id or 3
PAD_ID = asr_tokenizer.pad_token_id or 0

asr_model.eval()
print("Moonshine ASR loaded.")

print("Loading NLLB translation model...")
nllb_tokenizer = AutoTokenizer.from_pretrained(str(NLLB_MODEL_PATH), local_files_only=True)

nllb_model = AutoModelForSeq2SeqLM.from_pretrained(
    str(NLLB_MODEL_PATH),
    dtype=nllb_dtype,
    local_files_only=True
).to(device)

nllb_model.eval()
print("NLLB translator loaded.")


def send_to_nao(command):
    env = os.environ.copy()
    env["PYTHONPATH"] = NAOQI_PATH

    subprocess.call(
        [PYTHON2, NAO_SCRIPT, command],
        env=env
    )


def detect_command_from_bangla(text):
    text = text.lower().strip()

    commands = {
        "name": [
            "নাম", "তোমার নাম", "আপনার নাম", "তোমার নাম কি", "তোমার নাম কী",
            "আপনার নাম কি", "আপনার নাম কী", "কি নাম", "কী নাম", "নাম বল",
            "নাম বলো", "nam", "name"
        ],

        "sit": [
            "বস", "বসো", "বসুন", "বসে", "বসে পড়", "বসে পড়ো",
            "বসে পর", "বসে পরো", "বসে যাও", "sit", "bosho", "boso"
        ],

        "stand": [
            "দাঁড়াও", "দাড়াও", "দাড়া", "দাঁড়া", "উঠ", "উঠো",
            "উঠে দাঁড়াও", "উঠে দাড়াও", "দারাও", "daraw", "stand"
        ],

        "hello": [
            "হ্যালো", "হেলো", "হাই", "সালাম", "আসসালামু আলাইকুম",
            "hello", "hi", "hey"
        ],

        "walk_forward": [
            "সামনে যাও", "সামনে যাওয়া", "এগিয়ে যাও", "এগিয়ে যাও",
            "আগে যাও", "সোজা যাও", "সামনে", "forward", "go forward"
        ],

        "turn_left": [
            "বামে যাও", "বামে ঘুরো", "বাম দিকে যাও", "বাম দিকে ঘুরো",
            "লেফট", "left"
        ],

        "turn_right": [
            "ডানে যাও", "ডানে ঘুরো", "ডান দিকে যাও", "ডান দিকে ঘুরো",
            "রাইট", "right"
        ],

        "stop": [
            "থামো", "থাম", "স্টপ", "বন্ধ", "বন্ধ করো", "বন্ধ কর", "stop"
        ],

        "right_hand": [
            "ডান হাত", "ডানহাত", "ডান হাত নাড়াও", "ডান হাত নাড়াও",
            "হাত নাড়াও", "হাত নাড়াও", "ডান হাত উঠাও", "ডান হাত তোলো",
            "right hand", "wave"
        ],

        "left_hand": [
            "বাম হাত", "বামহাত", "বাম হাত নাড়াও", "বাম হাত নাড়াও",
            "বাম হাত উঠাও", "বাম হাত তোলো", "left hand"
        ],

        "rest": [
            "ঘুমাও", "ঘুম", "বিশ্রাম নাও", "বিশ্রাম", "রেস্ট", "rest", "sleep"
        ],

        "dance": [
            "নাচ", "নাচো", "নাচ কর", "dance"
        ],

        "ip_address": [
            "আইপি", "আইপি অ্যাড্রেস", "আইপি এড্রেস", "আইপি ঠিকানা",
            "ip", "ip address"
        ]
    }

    for command, keywords in commands.items():
        for keyword in keywords:
            if keyword in text:
                print("Exact match:", keyword)
                return command

    best_score = 0
    best_command = "unknown"
    best_keyword = ""

    for command, keywords in commands.items():
        for keyword in keywords:
            score = fuzz.partial_ratio(keyword.lower(), text.lower())

            if score > best_score:
                best_score = score
                best_command = command
                best_keyword = keyword

    print("Fuzzy best keyword:", best_keyword)
    print("Fuzzy score:", best_score)

    if best_score >= 80:
        return best_command

    return "unknown"


def record_audio(seconds=RECORD_SECONDS, sample_rate=RECORD_SAMPLE_RATE):
    print("\nSpeak Bangla now...")
    print("Wait 0.5 second, then speak clearly.")

    audio = sd.rec(
        int(seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        device=MIC_DEVICE
    )

    sd.wait()

    audio = np.squeeze(audio)

    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.95

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    write(temp_file.name, sample_rate, audio)
    write("last_live_input.wav", sample_rate, audio)

    return temp_file.name


def transcribe(audio_path):
    audio, _ = librosa.load(str(audio_path), sr=ASR_SAMPLE_RATE)

    silence = np.zeros(int(0.5 * ASR_SAMPLE_RATE), dtype=np.float32)
    audio = np.concatenate([silence, audio, silence])

    if len(audio) < ASR_SAMPLE_RATE * 0.4:
        return ""

    remainder = len(audio) % 320
    if remainder:
        audio = np.concatenate([
            audio,
            np.zeros(320 - remainder, dtype=np.float32)
        ])

    input_values = torch.tensor(audio).unsqueeze(0).to(device, dtype=asr_dtype)

    with torch.no_grad():
        generated_ids = asr_model.generate(
            input_values,
            max_new_tokens=80,
            num_beams=1,
            decoder_start_token_id=START_ID,
            pad_token_id=PAD_ID,
            eos_token_id=EOS_ID
        )

    bangla_text = asr_tokenizer.decode(
        generated_ids[0].tolist(),
        skip_special_tokens=True
    )

    return bangla_text.strip()


def translate_bn_to_en(bangla_text):
    if not bangla_text or not bangla_text.strip():
        return ""

    nllb_tokenizer.src_lang = "ben_Beng"

    inputs = nllb_tokenizer(
        bangla_text,
        return_tensors="pt"
    ).to(device)

    english_token_id = nllb_tokenizer.convert_tokens_to_ids("eng_Latn")

    with torch.no_grad():
        output = nllb_model.generate(
            **inputs,
            forced_bos_token_id=english_token_id,
            max_length=120,
            num_beams=3
        )

    english_text = nllb_tokenizer.batch_decode(
        output,
        skip_special_tokens=True
    )[0]

    return english_text.strip()


if __name__ == "__main__":
    print("\nLive Bangla ASR + NAO started.")
    print("Press Ctrl + C to stop.")
    print("Mic device:", MIC_DEVICE)
    print("Recording sample rate:", RECORD_SAMPLE_RATE)

    while True:
        audio_path = record_audio()

        bangla_text = transcribe(audio_path)

        if bangla_text:
            english_text = translate_bn_to_en(bangla_text)
            command = detect_command_from_bangla(bangla_text)
        else:
            english_text = ""
            command = "unknown"

        os.remove(audio_path)

        print("=" * 60)
        print("Bangla  :", bangla_text)
        print("English :", english_text)
        print("Command :", command)
        print("Debug audio saved as: last_live_input.wav")

        if command != "unknown":
            print("Sending command to NAO:", command)
            send_to_nao(command)
        else:
            print("No valid NAO command detected.")

        if device == "cuda":
            torch.cuda.empty_cache()