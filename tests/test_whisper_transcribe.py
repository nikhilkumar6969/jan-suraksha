"""
Tests for Offline AI Speech-to-Text with Multi-Mode Performance Tuning.
Verifies Mode A (Accuracy), Mode B (Balanced), and Mode C (Speed),
model caching, in-memory decoding, and API endpoints.
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
    transcribe_audio,
    MODE_ACCURACY,
    MODE_BALANCED,
    MODE_SPEED
)

SAMPLE_WAV = Path(__file__).resolve().parent.parent / "backend" / "models" / "sherpa-onnx-whisper-tiny" / "test_wavs" / "0.wav"

client = TestClient(app)


def test_model_directory_and_availability():
    """Verify that both Whisper Medium and Whisper Small models are accessible locally."""
    path_med = resolve_model_path("medium")
    assert is_model_available(path_med) is True, f"Medium model files missing at {path_med}"

    path_small = resolve_model_path("small")
    assert is_model_available(path_small) is True, f"Small model files missing at {path_small}"

    device, compute = get_optimal_device_and_compute()
    assert device in {"cpu", "cuda"}
    assert compute in {"int8", "float16"}


def test_singleton_model_loading():
    """Verify that get_whisper_model caches and reuses instances."""
    m_small_1 = get_whisper_model("small", auto_download=False)
    assert m_small_1 is not None
    m_small_2 = get_whisper_model("small", auto_download=False)
    assert m_small_1 is m_small_2, "Whisper Small model should be a cached singleton"

    m_med_1 = get_whisper_model("medium", auto_download=False)
    assert m_med_1 is not None
    m_med_2 = get_whisper_model("medium", auto_download=False)
    assert m_med_1 is m_med_2, "Whisper Medium model should be a cached singleton"


def test_transcribe_mode_b_balanced_default():
    """Verify default Mode B (Balanced) with Whisper Small and greedy decoding."""
    assert SAMPLE_WAV.exists(), "Sample test WAV file not found"

    res = transcribe_audio(SAMPLE_WAV, mode=MODE_BALANCED)
    assert res["success"] is True
    assert len(res["text"].strip()) > 0
    assert res["language"] == "en"
    assert res["mode"] == "balanced"
    assert "small" in res["model"]
    assert res["duration"] > 0
    assert res["processing_time"] > 0
    assert res["rtf"] > 0


def test_transcribe_mode_c_speed():
    """Verify Mode C (Speed) with Sherpa-ONNX Whisper Tiny and lowest latency."""
    res = transcribe_audio(SAMPLE_WAV, mode=MODE_SPEED)
    assert res["success"] is True
    assert len(res["text"].strip()) > 0
    assert res["mode"] == "speed"
    assert "tiny" in res["model"]
    assert res["duration"] > 0
    assert res["processing_time"] > 0
    assert res["rtf"] > 0


def test_transcribe_mode_a_accuracy():
    """Verify Mode A (Accuracy) with Whisper Medium and beam_size=5."""
    res = transcribe_audio(SAMPLE_WAV, mode=MODE_ACCURACY)
    assert res["success"] is True
    assert len(res["text"].strip()) > 0
    assert res["mode"] == "accuracy"
    assert "medium" in res["model"]
    assert res["duration"] > 0


def test_transcribe_with_manual_language():
    """Verify transcription with forced manual language parameter."""
    res = transcribe_audio(SAMPLE_WAV, language="en", mode=MODE_BALANCED)
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
    res_corrupt = transcribe_audio(b"NotAValidAudioStream1234567890", filename="corrupt.wav")
    assert res_corrupt["success"] is False
    assert "error" in res_corrupt


def test_api_transcribe_endpoint_modes():
    """Verify POST /api/transcribe supports mode selection while preserving backward compatibility."""
    wav_bytes = SAMPLE_WAV.read_bytes()

    # Default call (no mode provided -> defaults to balanced)
    resp_def = client.post(
        "/api/transcribe",
        files={"audio": ("sample.wav", io.BytesIO(wav_bytes), "audio/wav")},
        data={"language": "auto"}
    )
    assert resp_def.status_code == 200
    data_def = resp_def.json()
    assert data_def["success"] is True
    assert data_def["mode"] == "balanced"
    assert "processing_time" in data_def
    assert "rtf" in data_def

    # Explicit Speed Mode
    resp_speed = client.post(
        "/api/transcribe",
        files={"audio": ("sample.wav", io.BytesIO(wav_bytes), "audio/wav")},
        data={"language": "en", "mode": "speed"}
    )
    assert resp_speed.status_code == 200
    data_speed = resp_speed.json()
    assert data_speed["success"] is True
    assert data_speed["mode"] == "speed"


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
