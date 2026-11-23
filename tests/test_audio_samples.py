"""
Automated Unit and Integration Tests for Jan Suraksha Audio Sample Suite & Voice Alerts
Validates that:
1. All demonstration audio samples exist with valid WAV headers and proper size.
2. All 18 vernacular offline voice alert WAV files exist for Hindi, Chhattisgarhi, and English.
3. The /api/calls/transcribe endpoint processes sample audio and correctly flags scams while preserving genuine calls.
"""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = BASE_DIR / "frontend" / "assets" / "samples"
ALERTS_DIR = BASE_DIR / "frontend" / "assets" / "alerts"


def test_sample_audio_files_integrity():
    """Verify all 5 demo sample WAV files exist and have valid RIFF/WAVE headers."""
    expected_samples = [
        "cspdcl_electricity_call.wav",
        "digital_arrest_call.wav",
        "bank_kyc_call.wav",
        "fedex_customs_call.wav",
        "genuine_agriculture_call.wav"
    ]
    for sample_name in expected_samples:
        sample_path = SAMPLES_DIR / sample_name
        assert sample_path.exists(), f"Missing audio sample: {sample_name}"
        size = sample_path.stat().st_size
        assert size > 50_000, f"Sample {sample_name} is too small: {size} bytes"

        with open(sample_path, "rb") as f:
            header = f.read(12)
            assert header[:4] == b"RIFF", f"{sample_name} missing RIFF magic bytes"
            assert header[8:12] == b"WAVE", f"{sample_name} missing WAVE format header"


def test_offline_vernacular_voice_alerts_integrity():
    """Verify all 18 offline vernacular voice alert WAV files exist."""
    categories = ["upi_pin", "otp", "police", "remote_access", "extortion", "bank_kyc"]
    languages = ["hi", "chg", "en"]

    for cat in categories:
        for lang in languages:
            alert_filename = f"alert_{cat}_{lang}.wav"
            alert_path = ALERTS_DIR / alert_filename
            assert alert_path.exists(), f"Missing offline voice alert: {alert_filename}"
            size = alert_path.stat().st_size
            assert size > 30_000, f"Voice alert {alert_filename} is suspiciously small: {size} bytes"

            with open(alert_path, "rb") as f:
                header = f.read(12)
                assert header[:4] == b"RIFF", f"{alert_filename} invalid RIFF header"
                assert header[8:12] == b"WAVE", f"{alert_filename} invalid WAVE header"


def test_transcribe_cspdcl_electricity_sample():
    """Test /api/detect/call with CSPDCL electricity scam sample."""
    sample_path = SAMPLES_DIR / "cspdcl_electricity_call.wav"
    assert sample_path.exists()

    with open(sample_path, "rb") as f:
        response = client.post(
            "/api/detect/call",
            files={"audio": ("cspdcl_electricity_call.wav", f, "audio/wav")},
            data={"language": "hi"}
        )

    assert response.status_code == 200, f"Call detection failed: {response.text}"
    data = response.json()
    assert "verdict" in data
    assert "transcript" in data
    assert data["verdict"] in ["likely_scam", "unsure"]


def test_transcribe_genuine_agriculture_sample():
    """Test /api/detect/call with genuine agriculture mandi announcement."""
    sample_path = SAMPLES_DIR / "genuine_agriculture_call.wav"
    assert sample_path.exists()

    with open(sample_path, "rb") as f:
        response = client.post(
            "/api/detect/call",
            files={"audio": ("genuine_agriculture_call.wav", f, "audio/wav")},
            data={"language": "hi"}
        )

    assert response.status_code == 200, f"Call detection failed: {response.text}"
    data = response.json()
    assert "verdict" in data
    # Genuine announcement with no extortion/OTP demand should not be classified as likely_scam
    assert data["verdict"] in ["genuine", "unsure"]
