"""
Pytest Test Suite for Cryptographic Signed Update Pack (Ed25519)
"""

import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.updates.pack_signer import generate_signed_update_pack, verify_update_pack

def test_signed_update_pack_lifecycle():
    pack = generate_signed_update_pack()
    assert "pack_version" in pack
    assert "signature" in pack
    assert "public_key" in pack
    assert len(pack["signature"]) == 128  # 64-byte hex
    assert len(pack["public_key"]) == 64   # 32-byte hex

    # Verify signature
    is_valid = verify_update_pack(pack)
    assert is_valid is True

def test_tampered_pack_fails_verification():
    pack = generate_signed_update_pack()
    # Tamper with model version
    pack["model_version"] = "Malicious-Injected-Model-v999"
    is_valid = verify_update_pack(pack)
    assert is_valid is False
