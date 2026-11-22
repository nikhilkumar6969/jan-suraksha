"""
Ed25519 Signed Update Pack Generator and Verifier using PyNaCl
Produces tamper-evident rule pack and confirmed indicator blacklist.
"""

import json
from pathlib import Path
from datetime import datetime
import nacl.signing
import nacl.encoding
from app.reports.database import get_connection

KEY_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "ed25519_signing_key.bin"

def get_or_create_signing_key() -> nacl.signing.SigningKey:
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if KEY_PATH.exists():
        key_bytes = KEY_PATH.read_bytes()
        return nacl.signing.SigningKey(key_bytes)
    
    # Generate new 32-byte Ed25519 key
    signing_key = nacl.signing.SigningKey.generate()
    KEY_PATH.write_bytes(signing_key.encode())
    return signing_key

def generate_signed_update_pack() -> dict:
    signing_key = get_or_create_signing_key()
    verify_key = signing_key.verify_key
    verify_key_hex = verify_key.encode(encoder=nacl.encoding.HexEncoder).decode("utf-8")

    # Fetch confirmed indicators from database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT indicator_raw, scam_type, distinct_device_count 
        FROM indicators 
        WHERE status = 'Confirmed'
    """)
    rows = cursor.fetchall()
    blacklist = [
        {"indicator": r["indicator_raw"], "type": r["scam_type"], "reports": r["distinct_device_count"]}
        for r in rows
    ]
    conn.close()

    payload_data = {
        "pack_version": "2026.11.22-v1",
        "released_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"),
        "model_version": "Suraksha-Scam-LR-v1.0",
        "rules_version": "rules-2026-v2",
        "confirmed_blacklist": blacklist
    }

    # Canonical JSON string for signature
    canonical_bytes = json.dumps(payload_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signed = signing_key.sign(canonical_bytes)
    sig_hex = signed.signature.hex()

    pack = {
        **payload_data,
        "signature": sig_hex,
        "public_key": verify_key_hex
    }

    # Cache locally to backend/models/update_pack.json
    cache_path = KEY_PATH.parent / "update_pack.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(pack, f, indent=2)

    return pack

def verify_update_pack(pack: dict) -> bool:
    """Verifies that the pack has a valid Ed25519 signature."""
    try:
        sig_hex = pack["signature"]
        pub_key_hex = pack["public_key"]

        # Reconstruct canonical bytes without signature and public_key
        payload_data = {
            "pack_version": pack["pack_version"],
            "released_at": pack["released_at"],
            "model_version": pack["model_version"],
            "rules_version": pack["rules_version"],
            "confirmed_blacklist": pack["confirmed_blacklist"]
        }
        canonical_bytes = json.dumps(payload_data, sort_keys=True, separators=(",", ":")).encode("utf-8")

        verify_key = nacl.signing.VerifyKey(pub_key_hex, encoder=nacl.encoding.HexEncoder)
        sig_bytes = bytes.fromhex(sig_hex)
        verify_key.verify(canonical_bytes, sig_bytes)
        return True
    except Exception as e:
        return False
