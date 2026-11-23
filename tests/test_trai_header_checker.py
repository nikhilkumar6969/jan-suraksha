"""
Comprehensive Automated Test Suite for Offline TRAI SMS Sender Header & Smishing Guard
Validates:
1. Genuine Bank & Utility DLT Headers (GREEN)
2. 10-Digit Mobile Financial/Utility Impersonation (RED)
3. Typosquatting / Lookalike Headers (RED)
4. Brand-Domain Mismatch & Phishing URLs (RED)
5. Public URL Shorteners (AMBER/RED)
6. Malicious APK Distribution (RED)
7. Multilingual Hindi, Chhattisgarhi & English Explanation Accuracy
8. Combined ML Pipeline Score Fusion
9. REST API Endpoints (/api/detect/sms-header, /api/detect/message, /api/detect/sms-headers-db)
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.detect.trai_header import (
    parse_sender_id,
    levenshtein_distance,
    extract_domains_from_text,
    check_sender,
    load_headers_registry,
    combine_header_and_content_verdict
)
from backend.app.detect.pipeline import run_detection_pipeline

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Registry Integrity
# ---------------------------------------------------------------------------
def test_headers_registry_contains_at_least_30_brands():
    """Verify headers.json is loaded and contains at least 30 top Indian brands."""
    registry = load_headers_registry()
    assert "brands" in registry
    brands = registry["brands"]
    assert len(brands) >= 30, f"Expected at least 30 brands, found {len(brands)}"

    # Check key categories are present
    brand_types = {b.get("type") for b in brands}
    assert "bank" in brand_types
    assert "upi" in brand_types
    assert "telecom" in brand_types
    assert "government" in brand_types
    assert "courier" in brand_types
    assert "ecommerce" in brand_types


# ---------------------------------------------------------------------------
# Test 2: Sender Parsing Function
# ---------------------------------------------------------------------------
def test_parse_sender_id_trai_format():
    """Verify parsing standard 2-letter prefix, 6-char header, and suffixes."""
    p1 = parse_sender_id("AX-HDFCBK")
    assert p1["is_mobile"] is False
    assert p1["operator_prefix"] == "AX"
    assert p1["header"] == "HDFCBK"
    assert p1["suffix"] is None
    assert p1["is_trai_format"] is True

    p2 = parse_sender_id("VM-SBIINB-T")
    assert p2["operator_prefix"] == "VM"
    assert p2["header"] == "SBIINB"
    assert p2["suffix"] == "T"
    assert p2["is_trai_format"] is True

    p3 = parse_sender_id("BZ-AIRTEL-S")
    assert p3["operator_prefix"] == "BZ"
    assert p3["header"] == "AIRTEL"
    assert p3["suffix"] == "S"


def test_parse_sender_id_mobile_numbers():
    """Verify identification of 10-digit Indian mobile numbers in various notations."""
    # +91 prefix
    m1 = parse_sender_id("+919876543210")
    assert m1["is_mobile"] is True
    assert m1["mobile_number"] == "9876543210"

    # Leading zero
    m2 = parse_sender_id("09876543210")
    assert m2["is_mobile"] is True
    assert m2["mobile_number"] == "9876543210"

    # Plain 10 digits
    m3 = parse_sender_id("9876543210")
    assert m3["is_mobile"] is True
    assert m3["mobile_number"] == "9876543210"


# ---------------------------------------------------------------------------
# Test 3: Levenshtein Distance Lookalike Algorithm
# ---------------------------------------------------------------------------
def test_levenshtein_distance_metric():
    """Verify edit distance metric handles typosquatting."""
    assert levenshtein_distance("HDFCBK", "HDFCBK") == 0
    assert levenshtein_distance("HDFCBNK", "HDFCBK") == 1
    assert levenshtein_distance("SBIPAY", "SBIPSG") == 2
    assert levenshtein_distance("AIRTEL1", "AIRTEL") == 1


# ---------------------------------------------------------------------------
# Test 4: Genuine Bank OTP (GREEN)
# ---------------------------------------------------------------------------
def test_genuine_bank_otp_hdfc():
    """Verify authentic HDFC transaction alert is classified GREEN."""
    sender = "AX-HDFCBK-T"
    body = "Dear Customer, 482910 is your secret OTP for transaction of Rs. 4,500.00 at Amazon. Do NOT share this OTP with anyone."
    res = check_sender(sender, body, user_lang="hi")

    assert res["level"] == "GREEN"
    assert res["verdict"] == "genuine"
    assert res["matched_brand"] == "HDFC Bank"
    assert any(r["rule"] == "GENUINE_REGISTERED_HEADER" for r in res["reasons"])


def test_genuine_sbi_otp():
    """Verify official SBI transaction alert is classified GREEN."""
    sender = "VM-SBIINB"
    body = "930128 is OTP for your SBI net banking login. If not requested by you, call 1800112211. Bank never asks for OTP."
    res = check_sender(sender, body, user_lang="en")

    assert res["level"] == "GREEN"
    assert res["matched_brand"] == "State Bank of India (SBI)"


# ---------------------------------------------------------------------------
# Test 5: 10-Digit Mobile Financial Impersonation (RED)
# ---------------------------------------------------------------------------
def test_fake_sbi_kyc_from_mobile_number():
    """Verify 10-digit mobile claiming SBI KYC block is classified RED with critical reason."""
    sender = "+919876543210"
    body = "Dear customer your SBI bank account is blocked today. Please update PAN immediately to unblock: http://sbi-kyc.xyz"
    res = check_sender(sender, body, user_lang="hi")

    assert res["level"] == "RED"
    assert res["verdict"] == "likely_scam"
    assert res["score"] >= 0.85
    assert any(r["rule"] == "MOBILE_NUMBER_IMPERSONATION" for r in res["reasons"])
    assert "9876543210" in res["explanation"]


def test_electricity_disconnection_threat_from_mobile():
    """Verify power disconnection threat from 10-digit number is classified RED."""
    sender = "9827012345"
    body = "Dear consumer your electricity power will be disconnected tonight at 9:30 PM because bill not updated. Call electricity officer 9827012345."
    res = check_sender(sender, body, user_lang="hi")

    assert res["level"] == "RED"
    assert res["score"] >= 0.85
    assert any(r["rule"] == "MOBILE_NUMBER_IMPERSONATION" for r in res["reasons"])


# ---------------------------------------------------------------------------
# Test 6: Lookalike Header Typosquatting (RED)
# ---------------------------------------------------------------------------
def test_lookalike_hdfc_header():
    """Verify deceptive header 'HDFCBNK' (distance 1 from HDFCBK) triggers critical alert."""
    sender = "VM-HDFCBNK"
    body = "Your debit card has been suspended due to pending KYC update. Call customer care immediately."
    res = check_sender(sender, body, user_lang="hi")

    assert res["level"] == "RED"
    assert res["verdict"] == "likely_scam"
    assert any(r["rule"] == "LOOKALIKE_HEADER_TYPOSQUATTING" for r in res["reasons"])
    assert "HDFCBNK" in res["explanation"]


def test_lookalike_airtel_header():
    """Verify deceptive header 'AIRTEL1' (distance 1 from AIRTEL) triggers critical alert."""
    sender = "BZ-AIRTEL1"
    body = "Dear customer, your Airtel SIM KYC is expired. Re-verify now to avoid outgoing call block."
    res = check_sender(sender, body, user_lang="en")

    assert res["level"] == "RED"
    assert any(r["rule"] == "LOOKALIKE_HEADER_TYPOSQUATTING" for r in res["reasons"])


# ---------------------------------------------------------------------------
# Test 7: Brand-Domain Mismatch / Phishing Links (RED)
# ---------------------------------------------------------------------------
def test_brand_domain_mismatch_phishing():
    """Verify genuine header paired with external phishing domain triggers RED."""
    sender = "AX-HDFCBK"
    body = "Dear HDFC Customer, your reward points worth Rs 7,850 expire today. Claim cash credit at: http://hdfc-rewards-cash.xyz"
    res = check_sender(sender, body, user_lang="hi")

    assert res["level"] == "RED"
    assert any(r["rule"] == "BRAND_DOMAIN_MISMATCH" for r in res["reasons"])
    assert "hdfcbank.com" in res["explanation"] or "hdfc" in res["explanation"].lower()


# ---------------------------------------------------------------------------
# Test 8: Public URL Shorteners in Banking Alert (AMBER/RED)
# ---------------------------------------------------------------------------
def test_url_shortener_detection():
    """Verify concealed destinations via bit.ly are flagged."""
    sender = "VM-SBIINB"
    body = "Pre-approved loan of Rs 5,00,000 sanctioned for your account. Complete registration at https://bit.ly/sbi-quick-loan"
    res = check_sender(sender, body, user_lang="hi")

    assert res["score"] >= 0.40
    assert any(r["rule"] == "URL_SHORTENER_DETECTED" for r in res["reasons"])


# ---------------------------------------------------------------------------
# Test 9: Malicious APK Download (RED)
# ---------------------------------------------------------------------------
def test_malicious_apk_download():
    """Verify APK download prompt triggers critical penalty."""
    sender = "VM-SBIINB"
    body = "Mandatory security update: Download new YONO patch from http://yono-security.top/yono_app.apk"
    res = check_sender(sender, body, user_lang="en")

    assert res["level"] == "RED"
    assert any(r["rule"] == "MALICIOUS_APK_DOWNLOAD" for r in res["reasons"])


# ---------------------------------------------------------------------------
# Test 10: Chhattisgarhi Dialect Smishing from Mobile
# ---------------------------------------------------------------------------
def test_chhattisgarhi_subsidy_mobile_scam():
    """Verify Chhattisgarhi subsidy extortion sent from 10-digit number is caught."""
    sender = "+919755123456"
    body = "नमस्कार, महतारी वंदन योजना के 1000 रुपया तोर खाता म आए बर अटके हे। योजना राशि पाए बर तुरते 200 रुपया जमा करव अउ अपन गुप्त ओटीपी बताव।"
    res = check_sender(sender, body, user_lang="chg")

    assert res["level"] == "RED"
    assert any(r["rule"] == "MOBILE_NUMBER_IMPERSONATION" for r in res["reasons"])
    assert "9755123456" in res["explanation"]


# ---------------------------------------------------------------------------
# Test 11: Normal Non-Financial Message from Personal Mobile (SAFE/LOW)
# ---------------------------------------------------------------------------
def test_normal_personal_message_from_mobile():
    """Verify benign chat from friend on 10-digit mobile is not falsely marked RED."""
    sender = "+919826000000"
    body = "Kal subah 9 baje college ke gate par milte hain. Notes lete aana."
    res = check_sender(sender, body, user_lang="hi")

    assert res["level"] != "RED"
    assert res["score"] <= 0.35


# ---------------------------------------------------------------------------
# Test 12: India Post Genuine vs Fake Mobile
# ---------------------------------------------------------------------------
def test_india_post_official_header():
    """Verify official India Post DLT header is recognized."""
    sender = "DOPIND"
    body = "Your India Post consignment #CP123456789IN is out for delivery. OTP for delivery is 4021."
    res = check_sender(sender, body, user_lang="en")

    assert res["matched_brand"] == "India Post"
    assert res["level"] == "GREEN"


def test_india_post_fake_customs_mobile():
    """Verify fake India Post customs extortion from 10-digit mobile is RED."""
    sender = "+919826011122"
    body = "India Post Notice: Your parcel has been detained at customs hub. Pay Rs 25 redelivery charge at http://indiapost-update.site"
    res = check_sender(sender, body, user_lang="hi")

    assert res["level"] == "RED"
    assert any(r["rule"] == "MOBILE_NUMBER_IMPERSONATION" for r in res["reasons"])


# ---------------------------------------------------------------------------
# Test 13: DigiLocker Official Verification
# ---------------------------------------------------------------------------
def test_digilocker_official_header():
    """Verify official DigiLocker DLT header is recognized."""
    sender = "VM-DGLCKR"
    body = "719283 is your OTP to sign in to your DigiLocker account. OTP is confidential, do not share it."
    res = check_sender(sender, body, user_lang="hi")

    assert res["matched_brand"] == "DigiLocker"
    assert res["level"] == "GREEN"


# ---------------------------------------------------------------------------
# Test 14: End-to-End Pipeline Fusion with Sender
# ---------------------------------------------------------------------------
def test_run_detection_pipeline_with_sender_fusion():
    """Verify pipeline blends sender header check with ML text classification."""
    sender = "+919876543210"
    text = "Dear customer your bank account is blocked. Update KYC immediately."
    res = run_detection_pipeline(text, user_lang="hi", sender=sender)

    assert res["verdict"] == "likely_scam"
    assert "trai_header" in res
    assert res["trai_header"]["level"] == "RED"
    assert res["rule_flags"].get("trai_header_scam") is True


# ---------------------------------------------------------------------------
# Test 15: Fast API Endpoints
# ---------------------------------------------------------------------------
def test_api_sms_header_endpoint():
    """Verify POST /api/detect/sms-header endpoint."""
    response = client.post(
        "/api/detect/sms-header",
        json={
            "sender": "VM-HDFCBNK",
            "body": "Your account is blocked, call customer care immediately",
            "language": "hi"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "header_evaluation" in data
    assert data["header_evaluation"]["level"] == "RED"
    assert data["final_verdict"] == "likely_scam"


def test_api_detect_message_with_sender():
    """Verify POST /api/detect/message supports optional sender field."""
    response = client.post(
        "/api/detect/message",
        json={
            "text": "Your electricity line will be disconnected tonight.",
            "sender": "+919827011223",
            "language": "hi"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "likely_scam"
    assert "trai_header" in data
    assert data["trai_header"]["level"] == "RED"


def test_api_headers_db_endpoint():
    """Verify GET /api/detect/sms-headers-db returns cached brand database."""
    response = client.get("/api/detect/sms-headers-db")
    assert response.status_code == 200
    data = response.json()
    assert "brands" in data
    assert len(data["brands"]) >= 30
