"""
Pytest Test Suite for Suraksha Detection Pipeline
"""

import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.detect.pipeline import run_detection_pipeline
from app.detect.normalizer import normalize_text, detect_language

def test_language_detection():
    assert detect_language("This is an official electricity bill") == "en"
    assert detect_language("यह भारतीय स्टेट बैंक का संदेश है") == "hi"
    assert detect_language("Aapka yono account block ho gaya hai") == "hinglish"

def test_genuine_bank_otp_guard():
    # Legitimate bank OTPs with safety warnings must NOT be flagged as scam
    sms = "849201 is your secret OTP for transaction of Rs 1,450.00 at Amazon. DO NOT SHARE WITH ANYONE. Bank never calls to ask OTP."
    res = run_detection_pipeline(sms, user_lang="en")
    assert res["verdict"] == "genuine"
    assert res["rule_flags"]["is_genuine_alert"] is True
    assert res["rule_flags"]["explicit_otp_demand"] is False

def test_electricity_bill_scam():
    sms = "URGENT: CSPDCL Electricity officer notice. Your electricity power will be disconnected tonight at 9:30 PM. Call officer at 9876543210 immediately."
    res = run_detection_pipeline(sms, user_lang="hi")
    assert res["verdict"] == "likely_scam"
    assert res["confidence_percent"] >= 80
    assert len(res["risky_phrases"]) > 0

def test_digital_arrest_scam():
    sms = "CBI Crime Branch Notice: A parcel with narcotics and 5 passports found with your Aadhaar. You are under DIGITAL ARREST. Do not disconnect call. Pay clearance bond."
    res = run_detection_pipeline(sms, user_lang="en")
    assert res["verdict"] == "likely_scam"
    assert res["rule_flags"]["digital_arrest"] is True
    assert res["stages"]["current_stage"] >= 3

def test_hinglish_kyc_scam():
    sms = "Dear user, aapka SBI YONO account block ho gaya hai. KYC update karne ke liye turant link bit.ly/sbi-kyc par click kare."
    res = run_detection_pipeline(sms, user_lang="hi")
    assert res["verdict"] == "likely_scam"
    assert res["rule_flags"]["fake_kyc"] is True
