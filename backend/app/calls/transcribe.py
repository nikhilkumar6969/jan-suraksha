"""
Offline Call Audio Transcriber for Suraksha using Vosk
Handles 16kHz mono conversion and graceful fallback to manual transcript input.
"""

import os
import wave
import json
from pathlib import Path

VOSK_AVAILABLE = False
try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

def find_vosk_model(model_name: str = "vosk-model-small-hi") -> Path:
    models_dir = Path(__file__).resolve().parent.parent.parent / "models"
    candidates = [
        models_dir / model_name,
        models_dir / "vosk-model-small-en-in",
        Path.home() / ".cache" / "vosk" / model_name
    ]
    for c in candidates:
        if c.exists() and (c / "am").exists():
            return c
    return None

def transcribe_audio_file(file_path: Path) -> dict:
    if not VOSK_AVAILABLE:
        return {
            "success": False,
            "text": "",
            "notice": "Vosk library not available in environment. Please paste or type call transcript."
        }

    model_path = find_vosk_model()
    if not model_path:
        return {
            "success": False,
            "text": "",
            "notice": "Offline Vosk speech model not detected in backend/models/. You can paste or type call transcript directly."
        }

    try:
        wf = wave.open(str(file_path), "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in [8000, 16000]:
            return {
                "success": False,
                "text": "",
                "notice": "Audio must be 16kHz or 8kHz mono WAV. Please paste or upload transcript below."
            }

        model = vosk.Model(str(model_path))
        rec = vosk.KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                part = json.loads(rec.Result())
                if part.get("text"):
                    results.append(part["text"])

        final_part = json.loads(rec.FinalResult())
        if final_part.get("text"):
            results.append(final_part["text"])

        full_transcript = " ".join(results)
        return {
            "success": bool(full_transcript),
            "text": full_transcript,
            "notice": "Successfully transcribed using offline Vosk engine." if full_transcript else "No audible speech recognized."
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "notice": f"Audio processing notice: {str(e)}. Please paste call transcript below."
        }
