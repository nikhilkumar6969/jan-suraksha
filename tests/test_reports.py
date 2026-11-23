"""
Pytest Test Suite for Anonymous Reports and Indicator Confirmation Logic
"""

import sys
import uuid
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.reports.database import init_db, get_connection
from app.reports.service import submit_anonymous_report

def setup_module():
    init_db()

def test_report_confirmation_progression():
    # Indicator starts as Unconfirmed, transitions to Confirmed on 3 distinct devices
    unique_indicator = f"test_fraudster_{uuid.uuid4().hex[:8]}@okaxis"

    # Device 1 reports
    r1 = submit_anonymous_report(
        scam_type="Fake QR",
        district="Raipur",
        raw_indicator=unique_indicator,
        raw_device_id="device_alpha_1",
        confirmation_n=3
    )
    assert r1["success"] is True
    assert r1["status"] == "Unconfirmed"
    assert r1["distinct_devices"] == 1
    assert r1["confirmed"] is False

    # Device 2 reports
    r2 = submit_anonymous_report(
        scam_type="Fake QR",
        district="Raipur",
        raw_indicator=unique_indicator,
        raw_device_id="device_beta_2",
        confirmation_n=3
    )
    assert r2["success"] is True
    assert r2["status"] == "Unconfirmed"
    assert r2["distinct_devices"] == 2
    assert r2["confirmed"] is False

    # Device 3 reports -> Should CONFIRM!
    r3 = submit_anonymous_report(
        scam_type="Fake QR",
        district="Raipur",
        raw_indicator=unique_indicator,
        raw_device_id="device_gamma_3",
        confirmation_n=3
    )
    assert r3["success"] is True
    assert r3["status"] == "Confirmed"
    assert r3["distinct_devices"] == 3
    assert r3["confirmed"] is True

def test_deduplication():
    # Same device reporting same indicator twice within 24h is deduplicated
    unique_ind = f"dedupe_test_{uuid.uuid4().hex[:8]}"
    dev = "device_single_test"

    r1 = submit_anonymous_report("OTP Request", "Durg", unique_ind, dev)
    assert r1["success"] is True

    r2 = submit_anonymous_report("OTP Request", "Durg", unique_ind, dev)
    assert r2["success"] is True
    assert r2.get("deduplicated") is True

def test_hmac_secret_and_hashing(monkeypatch):
    from app.reports.service import hash_salted, get_report_hmac_secret
    import os

    # 1. Custom env secret
    custom_secret = "test_custom_env_secret_12345"
    monkeypatch.setenv("SURAKSHA_REPORT_SECRET", custom_secret)
    assert get_report_hmac_secret() == custom_secret.encode("utf-8")

    h1 = hash_salted("test_vpa@upi")
    assert len(h1) == 64  # SHA-256 hex digest
    # Consistent output
    assert h1 == hash_salted("  TEST_VPA@UPI  ")

    # 2. Secret change changes hash
    monkeypatch.setenv("SURAKSHA_REPORT_SECRET", "another_secret_67890")
    h2 = hash_salted("test_vpa@upi")
    assert h1 != h2

