"""
Tests for Offline AI Speech-to-Text with OpenAI Whisper Medium (faster-whisper)
Verifies local offline model loading, device selection, audio decoding, and API endpoints.
"""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.audio.whisper_service import (
    get_whisper_model,
    resolve_model_path,
    is_model_available,
    get_optimal_device_and_compute,
    transcribe_audio
)

SAMPLE_WAV = Path(__file__).resolve().parent.parent / "backend" / "models" / "sherpa-onnx-whisper-tiny" / "test_wavs" / "0.wav"

client = TestClient(app)

def test_model_directory_and_availability():
    """Verify that the Whisper Medium model is downloaded and accessible locally."""
    model_path = resolve_model_path()
    assert is_model_available(model_path) is True, f"Model files missing at {model_path}"
    
    device, compute = get_optimal_device_and_compute()
    assert device in {"cpu", "cuda"}
    assert compute in {"int8", "float16"}

def test_singleton_model_loading():
    """Verify that get_whisper_model loads the model once and reuses the instance."""
    m1 = get_whisper_model(auto_download=False)
    assert m1 is not None
    m2 = get_whisper_model(auto_download=False)
    assert m1 is m2, "Whisper model should be a cached singleton"

def test_transcribe_sample_wav_offline():
    """Verify local offline transcription of English test WAV."""
    assert SAMPLE_WAV.exists(), "Sample test WAV file not found"
    
    res = transcribe_audio(SAMPLE_WAV)
    assert res["success"] is True
    assert len(res["text"].strip()) > 0
    assert res["language"] == "en"
    assert res["language_probability"] >= 0.80
    assert res["duration"] > 0

def test_transcribe_with_manual_language():
    """Verify transcription with forced manual language parameter."""
    res = transcribe_audio(SAMPLE_WAV, language="en")
    assert res["success"] is True
    assert res["language"] == "en"

def test_transcribe_empty_and_invalid_audio():
    """Verify graceful handling for empty or corrupted audio payloads."""
    # 1. Empty bytes
    res_empty = transcribe_audio(b"")
    assert res_empty["success"] is False
    assert "empty" in res_empty["error"].lower()

    # 2. None input
    res_none = transcribe_audio(None)
    assert res_none["success"] is False
    assert "no audio" in res_none["error"].lower()

    # 3. Corrupt/random non-audio bytes
    res_corrupt = transcribe_audio(b"NotAFvalidAudioStream1234567890", filename="corrupt.wav")
    assert res_corrupt["success"] is False
    assert "error" in res_corrupt

def test_api_transcribe_endpoint_success():
    """Verify POST /api/transcribe with multipart audio file."""
    wav_bytes = SAMPLE_WAV.read_bytes()
    response = client.post(
        "/api/transcribe",
        files={"audio": ("sample.wav", io.BytesIO(wav_bytes), "audio/wav")},
        data={"language": "auto"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "text" in data
    assert len(data["text"]) > 0
    assert data["language"] == "en"
    assert data["language_probability"] > 0.8
    assert data["duration"] > 0

def test_api_transcribe_endpoint_validation_errors():
    """Verify POST /api/transcribe error handling for missing and empty files."""
    # Missing audio file
    resp_missing = client.post("/api/transcribe")
    assert resp_missing.status_code == 400
    assert resp_missing.json()["success"] is False

    # Empty audio file
    resp_empty = client.post(
        "/api/transcribe",
        files={"audio": ("empty.wav", io.BytesIO(b""), "audio/wav")}
    )
    assert resp_empty.status_code == 400
    assert resp_empty.json()["success"] is False
    assert "empty" in resp_empty.json()["error"].lower()
