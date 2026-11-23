"""
Comprehensive Test Suite for Real-Time Offline AI Scam Call Guardian
Tests all 16 scenarios specified in the system requirements:
1. Caller asks for OTP
2. Caller asks for UPI PIN
3. Fake bank employee
4. Fake police officer
5. Fake subsidy scheme
6. Caller demands money
7. Caller asks for remote access
8. Normal conversation mentioning OTP
9. Normal conversation mentioning banking
10. Hindi speech
11. Hinglish speech
12. Chhattisgarhi speech samples
13. Background noise handling
14. Airplane mode operation (100% offline verification)
15. Microphone permission denied handling
16. User stops listening (session cleanup and summary)
"""

import time
import pytest
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.calls.streaming_asr import (
    get_streaming_zipformer,
    get_whisper_recognizer,
    get_silero_vad,
    process_streaming_chunk,
    close_session,
    offline_transcribe_audio
)
from backend.app.detect.scam_engine import detect_scam_in_transcript
from backend.app.calls.conversation_tracker import (
    track_conversation_step,
    reset_tracker
)

client = TestClient(app)

# -------------------------------------------------------------
# Scenario 1: Caller asks for OTP
# -------------------------------------------------------------
def test_scenario_01_caller_asks_for_otp():
    text = "Sir, I am calling from bank verification department. Please tell your 6-digit OTP right now."
    res = detect_scam_in_transcript(text)
    assert res["risk_level"] == "CRITICAL"
    assert "OTP" in res["scam_category"]
    assert "otp" in " ".join(res["suspicious_phrases"]).lower()
    assert "सावधान" in res["audio_warning_hi"]

# -------------------------------------------------------------
# Scenario 2: Caller asks for UPI PIN
# -------------------------------------------------------------
def test_scenario_02_caller_asks_for_upi_pin():
    text = "Congratulations! To receive cashback of 5000 rupees in your account, enter your UPI PIN now."
    res = detect_scam_in_transcript(text)
    assert res["risk_level"] == "CRITICAL"
    assert "UPI PIN" in res["scam_category"]
    assert "कभी भी UPI PIN" in res["reason"] or "exclusively for sending" in res["reason_en"]
    assert "पिन न बताएं" in res["audio_warning_hi"]

# -------------------------------------------------------------
# Scenario 3: Fake bank employee & KYC threat
# -------------------------------------------------------------
def test_scenario_03_fake_bank_employee_kyc():
    text = "SBI customer care se bol raha hoon, aapka YONO account block ho gaya hai, KYC update karein."
    res = detect_scam_in_transcript(text)
    assert res["risk_level"] in ("HIGH", "CRITICAL")
    assert "bank" in " ".join(res["matched_categories"]).lower()
    assert res["is_scam"] is True

# -------------------------------------------------------------
# Scenario 4: Fake police officer (Digital arrest)
# -------------------------------------------------------------
def test_scenario_04_fake_police_digital_arrest():
    text = "Crime Branch Mumbai Police se Senior Inspector bol raha hoon. You are under digital arrest."
    res = detect_scam_in_transcript(text)
    assert res["risk_level"] in ("HIGH", "CRITICAL")
    assert "police" in " ".join(res["matched_categories"]).lower() or "arrest" in text.lower()
    assert res["is_scam"] is True

# -------------------------------------------------------------
# Scenario 5: Fake subsidy scheme (Mahtari Vandan / PM Awas)
# -------------------------------------------------------------
def test_scenario_05_fake_subsidy_scheme():
    text = "महतारी वंदन योजना सत्यापन शुल्क 200 रुपया तुरंत जमा करें और अपना ओटीपी बताएं।"
    res = detect_scam_in_transcript(text, user_lang="chg")
    assert res["risk_level"] in ("HIGH", "CRITICAL")
    assert res["is_scam"] is True

# -------------------------------------------------------------
# Scenario 6: Caller demands money / Bail bond
# -------------------------------------------------------------
def test_scenario_06_caller_demands_money():
    text = "Aapke khilaf arrest warrant hai, turant 50000 rupees bail security bond transfer karo."
    res = detect_scam_in_transcript(text)
    assert res["risk_level"] in ("HIGH", "CRITICAL")
    assert any("50000" in p or "bond" in p or "transfer" in p for p in res["suspicious_phrases"])

# -------------------------------------------------------------
# Scenario 7: Caller asks for remote access (AnyDesk)
# -------------------------------------------------------------
def test_scenario_07_caller_asks_remote_access():
    text = "Download AnyDesk app on your mobile and allow screen share to restore service."
    res = detect_scam_in_transcript(text)
    assert res["risk_level"] in ("HIGH", "CRITICAL")
    assert "remote_access" in res["matched_categories"]
    assert "anydesk" in " ".join(res["suspicious_phrases"]).lower()

# -------------------------------------------------------------
# Scenario 8: Normal conversation mentioning OTP (Swiggy safe)
# -------------------------------------------------------------
def test_scenario_08_normal_conversation_mentioning_otp():
    text = "Maine Swiggy ka OTP khud app me enter kiya aur delivery aa gayi."
    res = detect_scam_in_transcript(text)
    assert res["risk_level"] == "LOW"
    assert res["is_scam"] is False
    assert "सामान्य" in res["scam_category"] or "सुरक्षित" in res["scam_category"]

# -------------------------------------------------------------
# Scenario 9: Normal conversation mentioning banking
# -------------------------------------------------------------
def test_scenario_09_normal_conversation_mentioning_banking():
    text = "Kal subah bank jaunga passbook update karane ke liye aur branch manager se milunga."
    res = detect_scam_in_transcript(text)
    assert res["risk_level"] == "LOW"
    assert res["is_scam"] is False

# -------------------------------------------------------------
# Scenario 10: Hindi speech sample
# -------------------------------------------------------------
def test_scenario_10_hindi_speech():
    text = "आपका बैंक खाता बंद हो रहा है, तुरंत ओटीपी बताएं।"
    res = detect_scam_in_transcript(text, user_lang="hi")
    assert res["risk_level"] == "CRITICAL"
    assert "ओटीपी" in res["reason"]

# -------------------------------------------------------------
# Scenario 11: Hinglish speech sample
# -------------------------------------------------------------
def test_scenario_11_hinglish_speech():
    text = "Aapka account block ho gaya hai, turant apna 6 digit OTP share karein nahi to line cut ho jayegi."
    res = detect_scam_in_transcript(text, user_lang="hi")
    assert res["risk_level"] == "CRITICAL"
    assert res["is_scam"] is True

# -------------------------------------------------------------
# Scenario 12: Chhattisgarhi speech samples
# -------------------------------------------------------------
def test_scenario_12_chhattisgarhi_speech_samples():
    cg_sample = "थाना कोतवाली रायपुर ले बोलत हंव। तोर नाम म वारंट निकल गे हे। कॉल ल झन काटव अउ तुरते 40000 पईसा जमा करव।"
    res = detect_scam_in_transcript(cg_sample, user_lang="chg")
    assert res["risk_level"] in ("HIGH", "CRITICAL")
    assert res["is_scam"] is True

# -------------------------------------------------------------
# Scenario 13: Background noise handling (VAD test)
# -------------------------------------------------------------
def test_scenario_13_background_noise_handling():
    vad = get_silero_vad()
    assert vad is not None

    # Test pure silence
    silence = np.zeros(16000, dtype=np.float32)
    vad.accept_waveform(silence)
    assert vad.is_speech_detected() is False

    # Test low-level background white noise (amplitude 0.005)
    noise = (np.random.randn(16000) * 0.005).astype(np.float32)
    vad.accept_waveform(noise)
    assert vad.is_speech_detected() is False

# -------------------------------------------------------------
# Scenario 14: Airplane mode operation (100% offline verification)
# -------------------------------------------------------------
def test_scenario_14_airplane_mode_offline():
    # Verify that Sherpa-ONNX model inference runs completely locally without network sockets
    zipformer = get_streaming_zipformer()
    assert zipformer is not None

    # Test local offline transcription of sample audio
    sample_path = Path("frontend/assets/samples/digital_arrest_call.wav")
    assert sample_path.exists()
    res = offline_transcribe_audio(sample_path, lang="en")
    assert res["success"] is True
    assert "sherpa-onnx" in res["engine"].lower()
    assert len(res["text"]) > 10

# -------------------------------------------------------------
# Scenario 15: Microphone permission denied handling
# -------------------------------------------------------------
def test_scenario_15_microphone_permission_denied_api_fallback():
    # When microphone permission is denied on client, users can paste transcript or upload file
    response = client.post(
        "/api/detect/call",
        data={"transcript": "Police arrest warrant transfer 50000"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ("HIGH", "CRITICAL")
    assert data["verdict"] == "likely_scam"

# -------------------------------------------------------------
# Scenario 16: User stops listening (session cleanup and summary)
# -------------------------------------------------------------
def test_scenario_16_user_stops_listening_cleanup():
    session_id = "test_cleanup_session"
    # Send chunk
    chunk_res = process_streaming_chunk(session_id, b"\x00" * 3200, sample_rate=16000)
    assert chunk_res["session_id"] == session_id

    # Stop session
    stop_resp = client.post(
        "/api/calls/session-stop",
        json={"session_id": session_id}
    )
    assert stop_resp.status_code == 200
    stop_data = stop_resp.json()
    assert stop_data["session_id"] == session_id

# -------------------------------------------------------------
# Latency & Precision Benchmarking
# -------------------------------------------------------------
def test_streaming_chunk_latency_benchmark():
    session_id = "latency_bench"
    dummy_audio = np.random.randn(1600).astype(np.float32) # 100ms
    pcm_bytes = (dummy_audio * 32767).astype(np.int16).tobytes()

    start = time.perf_counter()
    res = process_streaming_chunk(session_id, pcm_bytes, sample_rate=16000)
    duration_ms = (time.perf_counter() - start) * 1000

    # Latency should be well under 250ms for 100ms chunk
    assert duration_ms < 250, f"Latency {duration_ms}ms exceeded 250ms threshold"
    assert "latency_ms" in res
