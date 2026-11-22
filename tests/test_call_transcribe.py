"""
Tests for Audio Transcriber and Call Scam Detection in Suraksha
"""

from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.calls.transcribe import find_vosk_model, transcribe_audio_file

client = TestClient(app)

def test_vosk_model_installed():
    """Verify offline Vosk models exist in backend/models."""
    model_path = find_vosk_model("en")
    assert model_path is not None, "Indian English Vosk model should be present"
    assert (model_path / "am").exists()

    hi_model = find_vosk_model("hi")
    assert hi_model is not None, "Hindi Vosk model should be present"
    assert (hi_model / "am").exists()

def test_transcribe_sample_audio_file():
    """Verify transcription on generated sample scam call."""
    sample_file = Path("frontend/assets/samples/digital_arrest_call.wav")
    assert sample_file.exists(), "Sample audio file should exist"

    res = transcribe_audio_file(sample_file, lang="en")
    assert res["success"] is True
    assert "arrest" in res["text"].lower() or "police" in res["text"].lower()
    assert "vosk" in res["notice"].lower()

def test_transcribe_sample_audio_auto():
    """Verify dual-model auto-detection selects correct language model."""
    sample_file = Path("frontend/assets/samples/digital_arrest_call.wav")
    res = transcribe_audio_file(sample_file, lang="auto")
    assert res["success"] is True
    assert res["detected_lang"] == "en"
    assert "arrest" in res["text"].lower() or "police" in res["text"].lower()

def test_detect_call_api_with_audio_upload():
    """Verify /api/detect/call with multipart audio upload."""
    sample_file = Path("frontend/assets/samples/bank_kyc_call.wav")
    assert sample_file.exists()

    with open(sample_file, "rb") as f:
        response = client.post(
            "/api/detect/call",
            files={"audio": ("bank_kyc_call.wav", f, "audio/wav")},
            data={"language": "en"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    assert "transcript" in data
    assert len(data["transcript"]) > 0
    assert "confidence_percent" in data
    assert data["verdict"] in ["likely_scam", "unsure"]
