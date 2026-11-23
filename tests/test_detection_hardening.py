"""
Regression and Hardening Verification Test Suite for Jan Suraksha Detection Engine
Verifies all 8 critical requirements:
1. Greetings remain GENUINE
2. Normal financial conversations are not automatically flagged
3. Genuine bank notifications are not classified as scams
4. OTP/PIN theft attempts are flagged as likely_scam
5. Digital arrest threats are flagged as likely_scam
6. Remote access scams (AnyDesk, QuickSupport) are flagged
7. Government authority impersonation is detected
8. Chhattisgarhi dialect expressions are correctly handled
"""

import pytest
from app.detect.pipeline import run_detection_pipeline

def test_01_greetings_remain_genuine():
    greetings = [
        ("hello", "en"),
        ("Hi", "en"),
        ("Good morning", "en"),
        ("Namaste", "en"),
        ("Kaise ho?", "hi"),
        ("Thank you", "en"),
        ("नमस्ते, आप कैसे हैं?", "hi"),
        ("जय जोहार संगवारी!", "chg"),
        ("कइसे हस भाई?", "chg")
    ]
    for text, lang in greetings:
        res = run_detection_pipeline(text, user_lang=lang)
        assert res["verdict"] == "genuine", f"Greeting '{text}' failed: got {res['verdict']}"
        assert res["confidence_percent"] >= 70, f"Confidence too low for '{text}': {res['confidence_percent']}%"
        assert len(res["risky_phrases"]) == 0, f"Risky phrases found for greeting '{text}': {res['risky_phrases']}"

def test_02_normal_financial_conversations_not_flagged():
    normal_fin = [
        ("I transferred money.", "en"),
        ("Your payment was received.", "en"),
        ("Please check your bank statement.", "en"),
        ("Your electricity bill is due.", "en"),
        ("I have already paid the school fees online.", "en"),
        ("मैंने अपना बिजली का बिल कल ही ऑनलाइन भर दिया है।", "hi"),
        ("मंय बिजली बिल पटा दे हंव, रसीद मिल गे हे।", "chg")
    ]
    for text, lang in normal_fin:
        res = run_detection_pipeline(text, user_lang=lang)
        assert res["verdict"] == "genuine", f"Normal financial '{text}' flagged as {res['verdict']}"

def test_03_genuine_bank_notifications_with_safety_guard():
    genuine_alerts = [
        ("458921 is your secret OTP for Amazon purchase. DO NOT SHARE WITH ANYONE. Bank never calls to ask OTP.", "en"),
        ("प्रिय ग्राहक, 123456 आपका गोपनीय OTP है। किसी के साथ साझा न करें। बैंक कभी OTP नहीं पूछता। -SBI", "hi"),
        ("ककरो ले अपन गुप्त ओटीपी झन बताव, बैंक कभू फोन म ओटीपी नइ मांगय।", "chg")
    ]
    for text, lang in genuine_alerts:
        res = run_detection_pipeline(text, user_lang=lang)
        assert res["verdict"] == "genuine", f"Bank notification '{text}' flagged as {res['verdict']}"
        assert res["confidence_percent"] >= 90, f"Confidence too low: {res['confidence_percent']}%"

def test_04_otp_and_pin_theft_detected():
    theft_cases = [
        ("Share your OTP.", "en"),
        ("Enter your UPI PIN to receive money.", "en"),
        ("अपना 6 अंकों का गुप्त OTP हमारे बैंक अधिकारी को बताएं।", "hi"),
        ("खाता म पईसा आही, मोबाइल निकालव अउ तुरते UPI पिन डारव।", "chg"),
        ("पैसे पाने के लिए अपना UPI पिन डालें।", "hi"),
        ("Share your Google Pay OTP to receive 1000 rupees cashback.", "en")
    ]
    for text, lang in theft_cases:
        res = run_detection_pipeline(text, user_lang=lang)
        assert res["verdict"] == "likely_scam", f"Theft '{text}' not flagged as scam: got {res['verdict']}"
        assert res["confidence_percent"] >= 90, f"Confidence should be high for theft: {res['confidence_percent']}%"

def test_05_digital_arrest_flagged():
    arrest_cases = [
        ("Pay immediately or police will arrest you.", "en"),
        ("CBI Cyber Crime notice: You are placed under DIGITAL ARREST. Pay clearance bond immediately.", "en"),
        ("क्राइम ब्रांच डिजिटल अरेस्ट: आपके पार्सल में ड्रग्स पकड़े गए हैं। तुरंत 30,000 रु जमानत भरें।", "hi"),
        ("डिजिटल अरेस्ट! तोर आधार कार्ड म नशीला दवाई पकड़ाए हे, पुलिस आही।", "chg")
    ]
    for text, lang in arrest_cases:
        res = run_detection_pipeline(text, user_lang=lang)
        assert res["verdict"] == "likely_scam", f"Digital arrest '{text}' failed: got {res['verdict']}"
        assert res["rule_flags"].get("digital_arrest") or res["combined_score"] >= 0.55

def test_06_remote_access_scams_flagged():
    remote_cases = [
        ("Install AnyDesk for bank verification.", "en"),
        ("Download QuickSupport APK from link to complete verification or SIM deactivated.", "en"),
        ("तुरंत AnyDesk ऐप डाउनलोड करें और 9 अंकों का कोड बताएं।", "hi"),
        ("AnyDesk ऐप डाउनलोड करव अउ अपन स्क्रीन शेयर करव।", "chg")
    ]
    for text, lang in remote_cases:
        res = run_detection_pipeline(text, user_lang=lang)
        assert res["verdict"] == "likely_scam", f"Remote scam '{text}' failed: got {res['verdict']}"

def test_07_government_authority_impersonation_detected():
    govt_cases = [
        ("CSPDCL notice: Unpaid bill pending. Call officer at 9876543210 to avoid cutoff.", "en"),
        ("CSPDCL अधिकारी बोलत हंव, बिजली चालू रखे बर तुरते 5000 रुपया ट्रांसफर करव।", "chg"),
        ("पुलिस थाना ले बोलत हंव, तोर नाम म वारंट हे, तुरते 20000 रुपया भेज नइ ते जेल जाबे।", "chg")
    ]
    for text, lang in govt_cases:
        res = run_detection_pipeline(text, user_lang=lang)
        assert res["verdict"] in ["likely_scam", "unsure"], f"Impersonation '{text}' not flagged: got {res['verdict']}"

def test_08_chhattisgarhi_dialect_expressions_handled():
    cg_cases = [
        ("का हाल चाल हे संगवारी? चाय पिए बर चलबो का?", "genuine"),
        ("कल गांव म धान कटाई के काम सुरू होही।", "genuine"),
        ("ए संगवारी, तोर लॉटरी लगे हे, मोबाइल के OTP ला तुरते भेज।", "likely_scam"),
        ("तोर महतारी वंदन योजना के पईसा रुके हे, पाए बर अपन एटीएम पिन बताव।", "likely_scam")
    ]
    for text, expected in cg_cases:
        res = run_detection_pipeline(text, user_lang="chg")
        assert res["verdict"] == expected, f"Chhattisgarhi '{text}' expected {expected}, got {res['verdict']}"
