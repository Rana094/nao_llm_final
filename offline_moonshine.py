import os
from pathlib import Path

# Force Hugging Face offline mode
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
import librosa
import numpy as np
from transformers import AutoTokenizer, AutoModelForSpeechSeq2Seq, AutoModelForSeq2SeqLM


# =========================
# PATHS
# =========================

BASE_DIR = Path(__file__).resolve().parent

ASR_MODEL_PATH = BASE_DIR / "models" / "moonshine-base-bn"
NLLB_MODEL_PATH = BASE_DIR / "models" / "nllb-200-distilled-600M"
AUDIO_DIR = BASE_DIR / "audio"

AUDIO_FILES = [
    "audio1.ogg",
    "audio2.ogg",
    "audio3.ogg",
    "audio4.ogg",
    "audio5.ogg",
    "audio6.ogg",
    "audio7.ogg",
]


# =========================
# CHECK PATHS
# =========================

if not ASR_MODEL_PATH.exists():
    raise FileNotFoundError(f"Moonshine model folder not found: {ASR_MODEL_PATH}")

if not NLLB_MODEL_PATH.exists():
    raise FileNotFoundError(f"NLLB model folder not found: {NLLB_MODEL_PATH}")

if not AUDIO_DIR.exists():
    raise FileNotFoundError(f"Audio folder not found: {AUDIO_DIR}")


# =========================
# DEVICE
# =========================

device = "cuda" if torch.cuda.is_available() else "cpu"
asr_dtype = torch.float16 if device == "cuda" else torch.float32
nllb_dtype = torch.float16 if device == "cuda" else torch.float32

print("Running fully offline")
print("Device:", device)


# =========================
# LOAD MOONSHINE ASR
# =========================

print("Loading Moonshine ASR model...")

asr_tokenizer = AutoTokenizer.from_pretrained(
    str(ASR_MODEL_PATH),
    local_files_only=True
)

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


# =========================
# LOAD NLLB TRANSLATOR
# =========================

print("Loading NLLB translation model...")

nllb_tokenizer = AutoTokenizer.from_pretrained(
    str(NLLB_MODEL_PATH),
    local_files_only=True
)

nllb_model = AutoModelForSeq2SeqLM.from_pretrained(
    str(NLLB_MODEL_PATH),
    dtype=nllb_dtype,
    local_files_only=True
).to(device)

nllb_model.eval()

print("NLLB translator loaded.")


# =========================
# COMMAND DETECTION
# =========================

def detect_command_from_bangla(text):
    text = text.lower().strip()

    commands = {
        "name": ["নাম", "তোমার নাম", "আপনার নাম", "nam", "name", "नाम"],
        "sit": ["বস", "বসো", "বসুন", "bosho", "sit"],
        "stand": ["দাঁড়াও", "দাড়াও", "দাড়া", "দাঁড়া", "উঠ", "উঠো", "darao", "stand"],
        "hello": ["হ্যালো", "সালাম", "hello", "hi", "hey"],
        "ip_address": ["আইপি", "আইপি অ্যাড্রেস", "আইপিাড্রেস", "ip", "ip address"],
        "right_hand": ["ডান হাত", "ডানহাত", "right hand", "dan hat"],
    }

    for command, keywords in commands.items():
        for keyword in keywords:
            if keyword in text:
                return command

    return "unknown"


# =========================
# ASR FUNCTION
# =========================

def transcribe(audio_path):
    audio, _ = librosa.load(str(audio_path), sr=16000)

    remainder = len(audio) % 320
    if remainder:
        audio = np.concatenate([
            audio,
            np.zeros(320 - remainder, dtype=np.float32)
        ])

    input_values = torch.tensor(audio).unsqueeze(0).to(
        device,
        dtype=asr_dtype
    )

    with torch.no_grad():
        generated_ids = asr_model.generate(
            input_values,
            max_new_tokens=2000,
            num_beams=5,
            no_repeat_ngram_size=3,
            repetition_penalty=1.2,
            decoder_start_token_id=START_ID,
            pad_token_id=PAD_ID,
            eos_token_id=EOS_ID
        )

    bangla_text = asr_tokenizer.decode(
        generated_ids[0].tolist(),
        skip_special_tokens=True
    )

    return bangla_text.strip()


# =========================
# TRANSLATION FUNCTION
# =========================

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
            max_length=200,
            num_beams=5
        )

    english_text = nllb_tokenizer.batch_decode(
        output,
        skip_special_tokens=True
    )[0]

    return english_text.strip()


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    print("ASR model path:", ASR_MODEL_PATH)
    print("NLLB model path:", NLLB_MODEL_PATH)
    print("Audio folder:", AUDIO_DIR)

    for audio_name in AUDIO_FILES:
        audio_path = AUDIO_DIR / audio_name

        print("=" * 60)

        if not audio_path.exists():
            print("Missing file:", audio_path)
            continue

        bangla_text = transcribe(audio_path)
        english_text = translate_bn_to_en(bangla_text)
        command = detect_command_from_bangla(bangla_text)

        print("Audio File :", audio_name)
        print("Bangla     :", bangla_text)
        print("English    :", english_text)
        print("Command    :", command)

        if device == "cuda":
            torch.cuda.empty_cache()