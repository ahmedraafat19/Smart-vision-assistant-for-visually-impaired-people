#!/usr/bin/env python3
import base64
import hashlib
import io
import json
import os
import re
import struct
import threading
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from PIL import Image
    from ultralytics import YOLO
except Exception as exc:
    Image = None
    YOLO = None
    CURRENCY_IMPORT_ERROR = str(exc)
else:
    CURRENCY_IMPORT_ERROR = ""


PROJECT_ROOT = Path(__file__).resolve().parent
MAX_JSON_BODY_BYTES = int(os.environ.get("MAX_JSON_BODY_BYTES", str(12 * 1024 * 1024)))
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", str(5 * 1024 * 1024)))
ALLOWED_ORIGINS = [origin.strip() for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
CURRENCY_CONFIDENCE_THRESHOLD = 0.94
CURRENCY_MARGIN_THRESHOLD = 0.55
CURRENCY_MIN_AGREEING_CROPS = 1

SECRET_PATTERNS = [
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]+"),
    re.compile(r"sk-[A-Za-z0-9_-]+"),
    re.compile(r"AIza[ A-Za-z0-9_-]+"),
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"(OPENROUTER_API_KEY|OPENAI_API_KEY|GEMINI_API_KEY|BACKEND_CLIENT_TOKEN|API_KEY)\s*[:=]\s*[^\s,}]+", re.IGNORECASE),
    re.compile(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+"),
    re.compile(r'"imageBase64"\s*:\s*"[A-Za-z0-9+/=]+"'),
    re.compile(r"[A-Za-z0-9+/=]{160,}"),
]


def redact_sensitive_text(value):
    text = str(value or "")
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text


def first_existing_path(paths):
    for path in paths:
        if path and path.exists():
            return path
    return None


def currency_root_candidates():
    env_root = os.environ.get("CURRENCY_ROOT", "").strip()
    downloads_root = Path.home() / "Downloads"
    return [
        Path(env_root).expanduser() if env_root else None,
        PROJECT_ROOT.parent / "currency model ",
        PROJECT_ROOT.parent / "testing" / "currency model ",
        downloads_root / "testing" / "currency model ",
        downloads_root / "currency model ",
    ]


def currency_model_candidates():
    env_model = (
        os.environ.get("CURRENCY_MODEL_PATH", "").strip()
        or os.environ.get("CURRENCY_MODEL", "").strip()
    )
    relative_candidates = [
        Path("runs/classify/currency-denomination-none-partial-n224/weights/best.pt"),
        Path("runs/classify/currency-denomination-none-n224/weights/best.pt"),
        Path("runs/classify/currency-denomination-n224-baseline/weights/best.pt"),
    ]
    candidates = [Path(env_model).expanduser() if env_model else None]
    for root in currency_root_candidates():
        if root:
            candidates.extend(root / relative_path for relative_path in relative_candidates)
    return candidates


def root_for_currency_model(model_path):
    if not model_path:
        return first_existing_path([path for path in currency_root_candidates() if path]) or PROJECT_ROOT

    parts = model_path.parts
    if "runs" in parts:
        return Path(*parts[: parts.index("runs")])
    return model_path.parent


CURRENCY_MODEL = first_existing_path(currency_model_candidates())
CURRENCY_ROOT = root_for_currency_model(CURRENCY_MODEL)
CURRENCY_PYTHON = CURRENCY_ROOT / ".venv" / "bin" / "python"
CURRENCY_YOLO_MODEL = None
CURRENCY_MODEL_LOAD_ERROR = ""
CURRENCY_MODEL_LOCK = threading.Lock()

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
    def handle_one_request(self):
        self.request_id = str(uuid.uuid4())
        super().handle_one_request()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path != "/health":
            self.send_json_error(404, "Not found", "not_found")
            return

        self.send_json(
            {
                "ok": True,
                "geminiTtsConfigured": bool(GEMINI_API_KEY),
                "currencyModelExists": bool(CURRENCY_MODEL and CURRENCY_MODEL.exists()),
                "currencyModelPath": str(CURRENCY_MODEL) if CURRENCY_MODEL else "",
                "currencyModelLoaded": bool(CURRENCY_YOLO_MODEL),
                "currencyModelLoadError": CURRENCY_MODEL_LOAD_ERROR,
                "currencyRuntime": "in_process_yolo",
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

        self.send_json_error(404, "Not found", "not_found")

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_JSON_BODY_BYTES:
            raise ValueError("Request body is too large")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def handle_tts(self):
        try:
            payload = self.read_json()
            text = str(payload.get("text", "")).strip()
            voice_option = str(payload.get("voiceOption", "female_ar")).strip()
            if not text:
                self.send_json_error(400, "text is required", "validation_error")
                return
            if voice_option not in VOICE_OPTIONS:
                self.send_json_error(400, "voiceOption must be male_en, female_en, male_ar, or female_ar", "validation_error")
                return
            if not GEMINI_API_KEY:
                self.send_json_error(500, "TTS provider is not configured", "tts_not_configured")
                return

            audio = generate_speech(text, voice_option)
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(audio)))
            self.end_headers()
            self.wfile.write(audio)
        except Exception as exc:
            print(f"tts_error requestId={self.request_id} error={redact_sensitive_text(exc)}")
            self.send_json_error(500, "TTS failed. Please try again.", "tts_failed")

    def handle_currency(self):
        try:
            payload = self.read_json()
            image_base64 = str(payload.get("imageBase64", "")).strip()
            if not image_base64:
                self.send_json_error(400, "imageBase64 is required", "validation_error")
                return

            if "," in image_base64 and "base64" in image_base64.split(",", 1)[0]:
                image_base64 = image_base64.split(",", 1)[1]

            image_bytes = base64.b64decode(image_base64)
            if len(image_bytes) > MAX_IMAGE_BYTES:
                self.send_json_error(413, "Image payload is too large", "image_too_large")
                return
            if not Image:
                self.send_json_error(500, "Currency runtime is not available", "currency_runtime_missing")
                return
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            result = classify_currency(image)
            print(
                "currency_result requestId=%s %s"
                % (
                    self.request_id,
                    redact_sensitive_text(json.dumps(currency_log_summary(result))),
                )
            )

            self.send_json(result)
        except Exception as exc:
            print(f"currency_error requestId={self.request_id} error={redact_sensitive_text(exc)}")
            self.send_json_error(500, "Currency recognition failed. Please try again.", "currency_failed")

    def send_json(self, payload, status=200):
        payload = {"requestId": getattr(self, "request_id", ""), **payload}
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json_error(self, status, message, code):
        self.send_json({"ok": False, "error": code, "message": message}, status=status)

    def send_cors_headers(self):
        origin = self.headers.get("Origin", "")
        if origin and origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        elif not ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("X-Request-Id", getattr(self, "request_id", ""))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")

    def log_message(self, fmt, *args):
        client_key = hashlib.sha256(self.address_string().encode("utf-8")).hexdigest()[:12]
        print("requestId=%s client=%s %s" % (getattr(self, "request_id", ""), client_key, redact_sensitive_text(fmt % args)))


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
        exc.read()
        raise RuntimeError("Gemini TTS failed") from exc

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


def load_currency_model():
    global CURRENCY_YOLO_MODEL
    global CURRENCY_MODEL_LOAD_ERROR

    if CURRENCY_YOLO_MODEL:
        return True
    if CURRENCY_IMPORT_ERROR:
        CURRENCY_MODEL_LOAD_ERROR = f"currency_runtime_import_failed: {CURRENCY_IMPORT_ERROR}"
        return False
    if not CURRENCY_MODEL or not CURRENCY_MODEL.exists():
        searched = [str(path) for path in currency_model_candidates() if path]
        CURRENCY_MODEL_LOAD_ERROR = "missing_currency_model; searched=" + "; ".join(searched)
        return False

    try:
        CURRENCY_YOLO_MODEL = YOLO(str(CURRENCY_MODEL))
        CURRENCY_MODEL_LOAD_ERROR = ""
        return True
    except Exception as exc:
        CURRENCY_YOLO_MODEL = None
        CURRENCY_MODEL_LOAD_ERROR = f"currency_model_load_failed: {redact_sensitive_text(exc)}"
        return False


def currency_crop_boxes(width, height):
    def box(name, left, top, right, bottom):
        left = max(0, int(left))
        top = max(0, int(top))
        right = min(width, int(right))
        bottom = min(height, int(bottom))
        return name, (left, top, right, bottom)

    return [
        box("full", 0, 0, width, height),
        box("center", width * 0.08, height * 0.25, width * 0.92, height * 0.92),
        box("bottom_center", width * 0.12, height * 0.48, width * 0.88, height),
        box("bottom_half", 0, height * 0.50, width, height),
        box("bottom_40", 0, height * 0.60, width, height),
        box("note_band", width * 0.03, height * 0.45, width * 0.97, height * 0.80),
        box("table_area", 0, height * 0.35, width * 0.75, height * 0.70),
        box("note_closeup", width * 0.30, height * 0.42, width * 0.78, height * 0.68),
        box("lower_left", 0, height * 0.42, width * 0.68, height),
        box("lower_right", width * 0.32, height * 0.42, width, height),
        box("middle_lower", width * 0.05, height * 0.38, width * 0.95, height * 0.86),
    ]


def prediction_from_yolo_result(prediction, crop_name):
    probs = prediction.probs
    names = prediction.names
    confidences = probs.data.detach().cpu().tolist()
    ranked = sorted(
        [
            {"label": str(names[index]), "confidence": float(confidence)}
            for index, confidence in enumerate(confidences)
        ],
        key=lambda item: item["confidence"],
        reverse=True,
    )
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else {"confidence": 0.0}
    margin = top["confidence"] - second["confidence"]
    label = top["label"]
    is_amount = label.isdigit()
    amount = int(label) if is_amount else None
    accepted = (
        is_amount
        and top["confidence"] >= CURRENCY_CONFIDENCE_THRESHOLD
        and margin >= CURRENCY_MARGIN_THRESHOLD
    )
    if accepted:
        reason = "accepted"
    elif not is_amount:
        reason = "top_label_is_not_amount"
    elif top["confidence"] < CURRENCY_CONFIDENCE_THRESHOLD:
        reason = "low_confidence"
    elif margin < CURRENCY_MARGIN_THRESHOLD:
        reason = "low_margin"
    else:
        reason = "rejected"

    return {
        "source": "backend_yolo",
        "crop": crop_name,
        "label": label,
        "amount": amount,
        "confidence": top["confidence"],
        "margin": margin,
        "accepted": accepted,
        "reason": reason,
        "topCandidates": ranked[:5],
    }


def pick_currency_prediction(results):
    candidates = sorted(
        results,
        key=lambda item: (item.get("confidence", 0), item.get("margin", 0)),
        reverse=True,
    )[:8]
    accepted = [item for item in results if item.get("accepted") and item.get("amount")]
    if not accepted:
        best = dict(candidates[0]) if candidates else {}
        return {
            **best,
            "accepted": False,
            "source": "backend_yolo",
            "reason": best.get("reason") or "no_strong_currency_crop",
            "candidates": candidates,
        }

    groups = {}
    for item in accepted:
        groups.setdefault(item["amount"], []).append(item)

    ranked_groups = sorted(
        [
            {
                "amount": amount,
                "items": items,
                "count": len(items),
                "best": sorted(
                    items,
                    key=lambda item: (item["margin"], item["confidence"]),
                    reverse=True,
                )[0],
            }
            for amount, items in groups.items()
        ],
        key=lambda group: (
            group["count"],
            group["best"]["margin"],
            group["best"]["confidence"],
        ),
        reverse=True,
    )
    best_group = ranked_groups[0]
    if best_group["count"] < CURRENCY_MIN_AGREEING_CROPS:
        best = dict(best_group["best"])
        return {
            **best,
            "accepted": False,
            "reason": "not_enough_currency_crop_agreement",
            "candidates": candidates,
        }

    best = dict(best_group["best"])
    return {
        **best,
        "accepted": True,
        "reason": "accepted",
        "consensusCount": best_group["count"],
        "candidates": candidates,
        "conflictAmounts": [group["amount"] for group in ranked_groups[1:]],
    }


def classify_currency(image):
    if not load_currency_model():
        return {
            "accepted": False,
            "source": "backend_yolo",
            "error": "currency_model_not_loaded",
            "reason": CURRENCY_MODEL_LOAD_ERROR or "currency_model_not_loaded",
        }

    width, height = image.size
    results = []
    for crop_name, crop_box in currency_crop_boxes(width, height):
        left, top, right, bottom = crop_box
        if right - left < 80 or bottom - top < 80:
            continue
        crop = image.crop((left, top, right, bottom))
        with CURRENCY_MODEL_LOCK:
            prediction = CURRENCY_YOLO_MODEL(crop, imgsz=224, verbose=False)[0]
        results.append(prediction_from_yolo_result(prediction, crop_name))

    if not results:
        return {
            "accepted": False,
            "source": "backend_yolo",
            "reason": "no_valid_currency_crops",
            "candidates": [],
        }

    return pick_currency_prediction(results)


def currency_log_summary(result):
    return {
        "accepted": result.get("accepted"),
        "source": result.get("source"),
        "label": result.get("label"),
        "amount": result.get("amount"),
        "confidence": result.get("confidence"),
        "margin": result.get("margin"),
        "crop": result.get("crop"),
        "reason": result.get("reason") or result.get("error"),
        "candidates": [
            {
                "crop": item.get("crop"),
                "label": item.get("label"),
                "amount": item.get("amount"),
                "confidence": item.get("confidence"),
                "margin": item.get("margin"),
                "accepted": item.get("accepted"),
                "reason": item.get("reason"),
            }
            for item in result.get("candidates", [])[:8]
        ],
    }


def main():
    load_currency_model()
    server = ThreadingHTTPServer(("0.0.0.0", 5055), GeminiBackendHandler)
    print("Gemini TTS and currency server running on http://0.0.0.0:5055")
    print("TTS configured:", bool(GEMINI_API_KEY))
    print("Currency model:", CURRENCY_MODEL or "not found")
    print("Currency model loaded:", bool(CURRENCY_YOLO_MODEL))
    if CURRENCY_MODEL_LOAD_ERROR:
        print("Currency model load error:", redact_sensitive_text(CURRENCY_MODEL_LOAD_ERROR))
    server.serve_forever()


if __name__ == "__main__":
    main()
