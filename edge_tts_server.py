#!/usr/bin/env python3
import base64
import json
import os
import struct
import subprocess
import tempfile
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
CURRENCY_ROOT = PROJECT_ROOT.parent / "currency model "
CURRENCY_PYTHON = CURRENCY_ROOT / ".venv" / "bin" / "python"
CURRENCY_MODEL = (
    CURRENCY_ROOT
    / "runs"
    / "classify"
    / "currency-denomination-none-partial-n224"
    / "weights"
    / "best.pt"
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_TTS_MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts").strip()
GEMINI_TTS_MALE_VOICE = os.environ.get("GEMINI_TTS_MALE_VOICE", "Charon").strip()
GEMINI_TTS_FEMALE_VOICE = os.environ.get("GEMINI_TTS_FEMALE_VOICE", "Kore").strip()
GEMINI_TTS_MALE_EN_VOICE = os.environ.get("GEMINI_TTS_MALE_EN_VOICE", GEMINI_TTS_MALE_VOICE).strip()
GEMINI_TTS_FEMALE_EN_VOICE = os.environ.get("GEMINI_TTS_FEMALE_EN_VOICE", GEMINI_TTS_FEMALE_VOICE).strip()
GEMINI_TTS_MALE_AR_VOICE = os.environ.get("GEMINI_TTS_MALE_AR_VOICE", GEMINI_TTS_MALE_VOICE).strip()
GEMINI_TTS_FEMALE_AR_VOICE = os.environ.get("GEMINI_TTS_FEMALE_AR_VOICE", GEMINI_TTS_FEMALE_VOICE).strip()

VOICE_OPTIONS = {
    "male_en": GEMINI_TTS_MALE_EN_VOICE,
    "female_en": GEMINI_TTS_FEMALE_EN_VOICE,
    "male_ar": GEMINI_TTS_MALE_AR_VOICE,
    "female_ar": GEMINI_TTS_FEMALE_AR_VOICE,
}


class GeminiBackendHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path != "/health":
            self.send_error(404)
            return

        self.send_json(
            {
                "ok": True,
                "geminiTtsConfigured": bool(GEMINI_API_KEY),
                "currencyModelExists": CURRENCY_MODEL.exists(),
                "voiceOptions": list(VOICE_OPTIONS.keys()),
            }
        )

    def do_POST(self):
        if self.path == "/tts":
            self.handle_tts()
            return

        if self.path == "/currency":
            self.handle_currency()
            return

        self.send_error(404)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def handle_tts(self):
        try:
            payload = self.read_json()
            text = str(payload.get("text", "")).strip()
            voice_option = str(payload.get("voiceOption", "female_ar")).strip()
            if not text:
                self.send_error(400, "text is required")
                return
            if voice_option not in VOICE_OPTIONS:
                self.send_error(400, "voiceOption must be male_en, female_en, male_ar, or female_ar")
                return
            if not GEMINI_API_KEY:
                self.send_error(500, "GEMINI_API_KEY is not configured on the backend")
                return

            audio = generate_speech(text, voice_option)
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(audio)))
            self.end_headers()
            self.wfile.write(audio)
        except Exception as exc:
            self.send_error(500, str(exc))

    def handle_currency(self):
        try:
            payload = self.read_json()
            image_base64 = str(payload.get("imageBase64", "")).strip()
            if not image_base64:
                self.send_error(400, "imageBase64 is required")
                return

            if "," in image_base64 and "base64" in image_base64.split(",", 1)[0]:
                image_base64 = image_base64.split(",", 1)[1]

            image_bytes = base64.b64decode(image_base64)
            with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
                image_file.write(image_bytes)
                image_file.flush()
                result = classify_currency(image_file.name)

            self.send_json(result)
        except Exception as exc:
            self.send_error(500, str(exc))

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


def generate_speech(text, voice_option):
    voice_name = VOICE_OPTIONS[voice_option]
    prompt = build_tts_prompt(text, voice_option)
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_TTS_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name,
                    }
                }
            },
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini TTS failed: {error_body}") from exc

    inline_data = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("inlineData", {})
    )
    audio_base64 = inline_data.get("data")
    if not audio_base64:
        raise RuntimeError("Gemini TTS returned no audio")

    audio_bytes = base64.b64decode(audio_base64)
    mime_type = inline_data.get("mimeType", "")
    if "wav" in mime_type:
        return audio_bytes
    return pcm_to_wav(audio_bytes)


def build_tts_prompt(text, voice_option):
    prompts = {
        "male_ar": (
            "Say this in a natural male Egyptian Arabic Cairo accent. "
            "Do not use formal Arabic. Speak clearly, calmly, and naturally "
            "because the user may be visually impaired:\n"
        ),
        "female_ar": (
            "Say this in a natural female Egyptian Arabic Cairo accent. "
            "Do not use formal Arabic. Speak clearly, calmly, and naturally "
            "because the user may be visually impaired:\n"
        ),
        "male_en": (
            "Say this in a natural male English voice. Speak clearly, calmly, "
            "and naturally because the user may be visually impaired:\n"
        ),
        "female_en": (
            "Say this in a natural female English voice. Speak clearly, calmly, "
            "and naturally because the user may be visually impaired:\n"
        ),
    }
    return prompts[voice_option] + text


def pcm_to_wav(pcm_bytes, sample_rate=24000, channels=1, bits_per_sample=16):
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = len(pcm_bytes)
    header = b"".join(
        [
            b"RIFF",
            struct.pack("<I", 36 + data_size),
            b"WAVE",
            b"fmt ",
            struct.pack("<I", 16),
            struct.pack("<H", 1),
            struct.pack("<H", channels),
            struct.pack("<I", sample_rate),
            struct.pack("<I", byte_rate),
            struct.pack("<H", block_align),
            struct.pack("<H", bits_per_sample),
            b"data",
            struct.pack("<I", data_size),
        ]
    )
    return header + pcm_bytes


def classify_currency(image_path):
    if not CURRENCY_MODEL.exists():
        return {"accepted": False, "error": f"Missing currency model: {CURRENCY_MODEL}"}

    python_bin = CURRENCY_PYTHON if CURRENCY_PYTHON.exists() else "python3"
    script = r"""
import json
import sys

from PIL import Image
from ultralytics import YOLO

model_path = sys.argv[1]
image_path = sys.argv[2]
model = YOLO(model_path)
image = Image.open(image_path).convert("RGB")
w, h = image.size

crop_boxes = [
    ("full", (0, 0, w, h)),
    ("center", (int(w * 0.08), int(h * 0.25), int(w * 0.92), int(h * 0.92))),
    ("bottom_center", (int(w * 0.12), int(h * 0.48), int(w * 0.88), h)),
    ("bottom_half", (0, int(h * 0.50), w, h)),
    ("bottom_40", (0, int(h * 0.60), w, h)),
    ("note_band", (int(w * 0.03), int(h * 0.62), int(w * 0.97), int(h * 0.94))),
    ("lower_left", (0, int(h * 0.42), int(w * 0.68), h)),
    ("lower_right", (int(w * 0.32), int(h * 0.42), w, h)),
    ("middle_lower", (int(w * 0.05), int(h * 0.38), int(w * 0.95), int(h * 0.86))),
]

results = []
for crop_name, box in crop_boxes:
    left, top, right, bottom = box
    if right - left < 80 or bottom - top < 80:
        continue
    crop = image.crop((left, top, right, bottom))
    prediction = model(crop, imgsz=224, verbose=False)[0]
    probs = prediction.probs
    names = prediction.names
    confidences = probs.data.detach().cpu().tolist()
    ranked = sorted(
        [{"label": str(names[index]), "confidence": float(confidence)}
         for index, confidence in enumerate(confidences)],
        key=lambda item: item["confidence"],
        reverse=True,
    )
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else {"confidence": 0.0}
    margin = top["confidence"] - second["confidence"]
    label = top["label"]
    is_amount = label.isdigit()
    results.append({
        "crop": crop_name,
        "label": label,
        "amount": int(label) if is_amount else None,
        "confidence": top["confidence"],
        "margin": margin,
        "accepted": is_amount and top["confidence"] >= 0.94 and margin >= 0.55,
    })

accepted = [item for item in results if item["accepted"]]
if accepted:
    groups = {}
    for item in accepted:
        groups.setdefault(item["amount"], []).append(item)
    ranked_groups = sorted(
        groups.items(),
        key=lambda entry: (
            len(entry[1]),
            max(item["margin"] for item in entry[1]),
            sum(item["confidence"] for item in entry[1]) / len(entry[1]),
        ),
        reverse=True,
    )
    best = dict(sorted(ranked_groups[0][1], key=lambda item: (item["margin"], item["confidence"]), reverse=True)[0])
    best["candidates"] = [dict(item) for item in results[:5]]
    print(json.dumps(best))
    raise SystemExit

relaxed = [
    item for item in results
    if item["amount"] is not None and item["confidence"] >= 0.40 and item["margin"] >= 0.20
]
if relaxed:
    groups = {}
    for item in relaxed:
        groups.setdefault(item["amount"], []).append(item)
    ranked_groups = sorted(
        groups.items(),
        key=lambda entry: (
            len(entry[1]),
            max(item["margin"] for item in entry[1]),
            sum(item["confidence"] for item in entry[1]) / len(entry[1]),
        ),
        reverse=True,
    )
    if len(ranked_groups[0][1]) < 2:
        best = dict(sorted(results, key=lambda item: (item["confidence"], item["margin"]), reverse=True)[0])
        print(json.dumps({"accepted": False, **best, "candidates": [dict(item) for item in results[:5]]}))
        raise SystemExit
    best = dict(sorted(ranked_groups[0][1], key=lambda item: (item["margin"], item["confidence"]), reverse=True)[0])
    best["accepted"] = True
    best["relaxed"] = True
    best["candidates"] = [dict(item) for item in results[:5]]
    print(json.dumps(best))
    raise SystemExit

best = dict(sorted(results, key=lambda item: (item["confidence"], item["margin"]), reverse=True)[0]) if results else {}
print(json.dumps({"accepted": False, **best, "candidates": [dict(item) for item in results[:5]]}))
"""
    process = subprocess.run(
        [str(python_bin), "-c", script, str(CURRENCY_MODEL), image_path],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(CURRENCY_ROOT),
        timeout=30,
    )
    if process.returncode != 0:
        return {"accepted": False, "error": process.stderr.strip() or process.stdout.strip()}

    return json.loads(process.stdout.strip().splitlines()[-1])


def main():
    server = ThreadingHTTPServer(("0.0.0.0", 5055), GeminiBackendHandler)
    print("Gemini TTS and currency server running on http://0.0.0.0:5055")
    print("TTS configured:", bool(GEMINI_API_KEY))
    server.serve_forever()


if __name__ == "__main__":
    main()
