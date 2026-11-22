"""
Pytest Test Suite for Suraksha Fake-QR Checker
"""

import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.qr.checker import parse_upi_uri, analyze_upi_qr

def test_parse_valid_upi():
    raw = "upi://pay?pa=shopkeeper@sbi&pn=Kirana%20Store&am=150.00&cu=INR"
    parsed = parse_upi_uri(raw)
    assert parsed["valid"] is True
    assert parsed["pa"] == "shopkeeper@sbi"
    assert parsed["pn"] == "Kirana Store"
    assert parsed["am"] == "150.00"

def test_qr_mismatch_detection():
    # Payee Name claims government utility CSPDCL, but handle is a personal user
    raw = "upi://pay?pa=rohitkumar982@okaxis&pn=CSPDCL%20Electricity%20Bill&am=2450.00"
    res = analyze_upi_qr(raw, user_lang="en")
    assert res["verdict"] == "likely_scam"
    assert any("MISMATCH" in w for w in res["warnings"])
    assert res["risk_score"] >= 0.7

def test_disguised_collect_request():
    raw = "upi://pay?pa=fraudster@paytm&pn=OLX%20Payment&am=5000&mode=02"
    res = analyze_upi_qr(raw, user_lang="en")
    assert res["verdict"] == "likely_scam"
    assert any("COLLECT" in w for w in res["warnings"])

def test_genuine_merchant_qr():
    raw = "upi://pay?pa=verma.kirana@sbi&pn=Verma%20General%20Store&cu=INR"
    res = analyze_upi_qr(raw, user_lang="en")
    assert res["verdict"] == "genuine"
    assert res["risk_score"] == 0.0
