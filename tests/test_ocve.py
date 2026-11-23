"""
Unit Tests for Official Communication Verification Engine (OCVE)
Verifies:
1. All 4 Evidence-Based Classification Statuses
2. Strict Non-100% Authenticity Guarantees
3. Independent Multi-Pillar Breakdown (4 Pillars)
4. Unavailable Context & Telemetry Transparency
5. Multilingual Output (English, Hindi, Hinglish/Chhattisgarhi)
6. Potential Impersonation & Spoofing Detection
7. Zero-Regression Integration with Pipeline & FastAPI API
"""

import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.detect.ocve import (
    verify_communication,
    EvidenceStatus,
    evaluate_sender_pillar,
    evaluate_url_pillar,
    evaluate_security_demands_pillar,
    evaluate_context_limits_pillar
)
from app.detect.pipeline import run_detection_pipeline


def test_evidence_based_classifications_presence():
    """Verify all 4 status definitions exist and match requirements."""
    assert EvidenceStatus.CONSISTENT.value == "Consistent with verified communication patterns"
    assert EvidenceStatus.SUSPICIOUS.value == "Suspicious communication patterns detected"
    assert EvidenceStatus.POTENTIAL_IMPERSONATION.value == "Potential impersonation detected"
    assert EvidenceStatus.INSUFFICIENT_INFO.value == "Insufficient information to verify"


def test_never_claims_100_percent_authentic():
    """
    CRITICAL MANDATE: Never declare an SMS, sender ID, URL, or communication
    100% genuine, authentic, or safe.
    """
    sample_texts = [
        ("SBI: Your A/C 1234 credited with INR 5,000. Ref 9021820.", "AD-SBIINB"),
        ("CSPDCL: Bill of Rs 850 paid successfully for BP 10029381.", "CP-CSPDCL"),
        ("HDFC Bank OTP is 492019 for transaction. Do not share with anyone.", "VM-HDFCBK"),
        ("Hello, please find the meeting notes attached.", None),
        ("Dear user, electricity power will be cut tonight.", "+919876543210")
    ]

    for text, sender in sample_texts:
        res = verify_communication(text, sender=sender, user_lang="en")
        # Assert strictly false
        assert res["is_100_percent_authentic"] is False
        assert res["authenticity_claim_prohibited"] is True

        # Assert no 100% claims in status strings
        assert "100%" not in res["overall_status"]
        assert "100% genuine" not in res["overall_status"].lower()
        assert "100% safe" not in res["overall_status"].lower()

        # Check all pillar statuses
        for pillar_key, pillar_val in res["pillars"].items():
            status_str = str(pillar_val.get("status", "")).lower()
            assert "100%" not in status_str
            assert "100% genuine" not in status_str
            assert "100% safe" not in status_str


def test_multi_pillar_independent_breakdown():
    """
    Ensure all 4 pillars are evaluated independently:
    1. sender_authenticity
    2. url_integrity
    3. security_demands
    4. context_limits
    """
    res = verify_communication(
        text="SBI alert: Update KYC at https://sbi-update.xyz or account suspended.",
        sender="AD-SBIINB",
        user_lang="en"
    )

    pillars = res["pillars"]
    assert "sender_authenticity" in pillars
    assert "url_integrity" in pillars
    assert "security_demands" in pillars
    assert "context_limits" in pillars

    # Sender matched legitimate SBI header
    assert pillars["sender_authenticity"]["status"] == EvidenceStatus.CONSISTENT.value

    # URL is an unaffiliated / lookalike link -> Impersonation detected
    assert pillars["url_integrity"]["status"] == EvidenceStatus.POTENTIAL_IMPERSONATION.value

    # Urgent panic pressure detected
    assert pillars["security_demands"]["status"] == EvidenceStatus.SUSPICIOUS.value

    # Context limits informative pillar
    assert len(pillars["context_limits"]["unavailable_telemetry"]) > 0


def test_potential_impersonation_detection():
    """Verify 10-digit mobile number claiming official banking/utility is detected."""
    res = verify_communication(
        text="Dear customer, your CSPDCL electricity line will be disconnected tonight. Call 9876543210.",
        sender="+919876543210",
        user_lang="en"
    )

    assert res["overall_status"] == EvidenceStatus.POTENTIAL_IMPERSONATION.value
    assert res["pillars"]["sender_authenticity"]["status"] == EvidenceStatus.POTENTIAL_IMPERSONATION.value
    assert "10-Digit Mobile" in res["pillars"]["sender_authenticity"]["indicators_present"][0]


def test_prohibited_credential_demand_detection():
    """Verify explicit OTP demand triggers suspicious classification."""
    res = verify_communication(
        text="Dear user, share your OTP immediately to receive your cashback reward of Rs 2000.",
        sender="AD-SBIINB",
        user_lang="en"
    )

    assert res["overall_status"] == EvidenceStatus.SUSPICIOUS.value
    assert res["pillars"]["security_demands"]["status"] == EvidenceStatus.SUSPICIOUS.value
    assert "Explicit OTP" in res["pillars"]["security_demands"]["indicators_present"][0]


def test_insufficient_information_handling():
    """Verify vague or unidentifiable message without sender returns insufficient info."""
    res = verify_communication(
        text="Meeting scheduled at 4pm tomorrow.",
        sender=None,
        user_lang="en"
    )

    assert res["overall_status"] == EvidenceStatus.INSUFFICIENT_INFO.value
    assert res["pillars"]["sender_authenticity"]["status"] == EvidenceStatus.INSUFFICIENT_INFO.value


def test_unavailable_information_transparency():
    """Verify system explicitly documents what telemetry is unavailable."""
    res = verify_communication(
        text="Your account statement is ready.",
        sender="VM-HDFCBK",
        user_lang="en"
    )

    unavail = res["unavailable_information"]
    assert len(unavail) > 0
    # Must report missing carrier cryptographic proof / SMPP signature
    joined = " ".join(unavail).lower()
    assert "carrier" in joined or "smpp" in joined or "cryptographic" in joined or "telecom" in joined


def test_multilingual_explainability():
    """Verify localized statuses, recommendations, and disclaimers in EN, HI, and CHG."""
    for lang in ["en", "hi", "chg"]:
        res = verify_communication(
            text="बिजली बिल भुगतान सफल रहा।",
            sender="CP-CSPDCL",
            user_lang=lang
        )
        assert len(res["overall_status_localized"]) > 0
        assert len(res["actionable_recommendations"]) > 0
        assert len(res["security_disclaimer"]) > 0


def test_pipeline_integration_preserves_existing_keys():
    """Verify pipeline output retains all existing fields while adding modular 'ocve'."""
    text = "Dear customer, your SBI account is blocked. Call 9876543210 immediately."
    pipeline_res = run_detection_pipeline(text, user_lang="en", sender="AD-SBIINB")

    # Assert existing schema keys are completely preserved
    expected_legacy_keys = [
        "verdict",
        "confidence_percent",
        "calibrated_confidence",
        "model_probability",
        "rule_risk",
        "combined_score",
        "explanation",
        "highlighted_html",
        "risky_phrases",
        "safe_phrases",
        "top_ngrams",
        "stages",
        "rule_flags",
        "lookalike_findings",
        "reputation_match",
        "trai_header",
        "input_language"
    ]
    for key in expected_legacy_keys:
        assert key in pipeline_res, f"Missing legacy key: {key}"

    # Assert new modular OCVE object is present
    assert "ocve" in pipeline_res
    ocve = pipeline_res["ocve"]
    assert ocve["is_100_percent_authentic"] is False
    assert ocve["overall_status"] in [
        EvidenceStatus.CONSISTENT.value,
        EvidenceStatus.SUSPICIOUS.value,
        EvidenceStatus.POTENTIAL_IMPERSONATION.value,
        EvidenceStatus.INSUFFICIENT_INFO.value
    ]


def test_api_ocve_endpoint():
    """Test the /api/detect/ocve endpoint using FastAPI TestClient."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/detect/ocve",
        json={"text": "OTP 192837 for your transaction. Do not share.", "sender": "AD-SBIINB", "language": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "Official Communication Verification Engine (OCVE)"
    assert data["is_100_percent_authentic"] is False
    assert "pillars" in data
    assert "sender_authenticity" in data["pillars"]
