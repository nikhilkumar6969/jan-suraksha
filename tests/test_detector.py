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
    assert detect_language("तोर बिजली बिल नइ भरे हस आज संझा लाइन कट जाही") == "chg"
    assert detect_language("tor bijli line kat jahi bill pataw") == "chg"

def test_chhattisgarhi_bijli_scam():
    sms = "तोर बिजली बिल नइ भरे हस, आज संझा 9:30 बजे लाइन कट जाही। तुरते 9827012345 म फोन लगाके पईसा पटाव।"
    res = run_detection_pipeline(sms, user_lang="chg")
    assert res["verdict"] == "likely_scam"
    assert res["rule_flags"]["fake_kyc"] is True
    assert res["rule_flags"]["urgency_pressure"] is True

def test_chhattisgarhi_police_arrest_scam():
    sms = "थाना कोतवाली रायपुर ले बोलत हंव। तोर नाम म वारंट निकल गे हे। कॉल ल झन काटव, वीडियो कॉल म बने रहव अउ तुरते पईसा जमा करव।"
    res = run_detection_pipeline(sms, user_lang="chg")
    assert res["verdict"] == "likely_scam"
    assert res["rule_flags"]["digital_arrest"] is True
    assert res["stages"]["current_stage"] >= 3

def test_hinglish_police_call_scam():
    from app.calls.analyzer import analyze_call_transcript
    call = "Main Crime Branch Mumbai Police se Senior Inspector bol raha hoon. Aapke khilaf Money Laundering aur arrest warrant jari hua hai. Phone cut mat karna, ghar ke andar raho aur turant 50000 rupaye bail security bond transfer karo."
    res = analyze_call_transcript(call, user_lang="hi")
    assert res["verdict"] == "likely_scam"
    assert res["confidence_percent"] >= 90
    assert res["rule_flags"]["digital_arrest"] is True

def test_genuine_bank_otp_guard():
    # Legitimate bank OTPs with safety warnings must NOT be flagged as scam
    sms = "849201 is your secret OTP for transaction of Rs 1,450.00 at Amazon. DO NOT SHARE WITH ANYONE. Bank never calls to ask OTP."
    res = run_detection_pipeline(sms, user_lang="en")
    assert res["verdict"] == "genuine"
    assert res["rule_flags"]["is_genuine_alert"] is True
    assert res["rule_flags"]["explicit_otp_demand"] is False

def test_genuine_bank_otp_multilingual_guard():
    # Hindi genuine bank alert
    sms_hi = "582910 आपका गुप्त OTP है लेन-देन रु 450 के लिए। किसी को न बताएं। बैंक कभी भी OTP नहीं पूछता।"
    res_hi = run_detection_pipeline(sms_hi, user_lang="hi")
    assert res_hi["verdict"] == "genuine"
    assert res_hi["rule_flags"]["is_genuine_alert"] is True

    # Chhattisgarhi genuine bank alert
    sms_chg = "918234 तोर बैंक लेन-देन के OTP हे। ककरो ले साझा झन करव। बैंक कभू घलो OTP नइ मांगय।"
    res_chg = run_detection_pipeline(sms_chg, user_lang="chg")
    assert res_chg["verdict"] == "genuine"
    assert res_chg["rule_flags"]["is_genuine_alert"] is True

def test_fraudulent_otp_demands_flagged():
    # Fraudulent demand for OTP with urgency must be flagged as scam
    sms_fraud = "Bank Officer Calling: Send your 6-digit OTP to 9876543210 immediately to verify and unfreeze your bank account."
    res_fraud = run_detection_pipeline(sms_fraud, user_lang="en")
    assert res_fraud["verdict"] == "likely_scam"
    assert res_fraud["rule_flags"]["explicit_otp_demand"] is True

    # Chhattisgarhi fraudulent OTP demand with urgency
    sms_fraud_chg = "बैंक मैनेजर: तुरंत मोबाइल म आए OTP ल बताव नइ ते तोर खाता बंद हो जाही।"
    res_fraud_chg = run_detection_pipeline(sms_fraud_chg, user_lang="chg")
    assert res_fraud_chg["verdict"] == "likely_scam"
    assert res_fraud_chg["rule_flags"]["explicit_otp_demand"] is True

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
