"""
Anonymous Report Ingestion and Abuse Prevention Service
- Deduplicates reports per (device_hash, indicator_hash)
- Rate limits per device per hour (max 10 reports/hr)
- Confirms indicators once N distinct devices report it (default N=3)
- Never stores message text or personal data
"""

import hashlib
from datetime import datetime, timedelta, timezone
from app.reports.database import get_connection

DEFAULT_CONFIRMATION_THRESHOLD = 3
MAX_REPORTS_PER_HOUR = 10
SALT = "SURAKSHA_CHHATTISGARH_2026_SALT"

def hash_salted(value: str) -> str:
    """Hashes device ID or indicator with a security salt."""
    return hashlib.sha256(f"{SALT}_{value.strip().lower()}".encode("utf-8")).hexdigest()

def submit_anonymous_report(scam_type: str, district: str, raw_indicator: str, raw_device_id: str, confirmation_n: int = DEFAULT_CONFIRMATION_THRESHOLD) -> dict:
    if not scam_type or not district or not raw_indicator:
        return {"success": False, "error": "Missing required report parameters"}

    indicator_clean = raw_indicator.strip()
    indicator_hash = hash_salted(indicator_clean)
    device_hash = hash_salted(raw_device_id)

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Rate Limiting Check: max reports per device in past 1 hour
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM reports 
        WHERE device_hash = ? AND created_at >= ?
    """, (device_hash, one_hour_ago))
    recent_cnt = cursor.fetchone()["cnt"]

    if recent_cnt >= MAX_REPORTS_PER_HOUR:
        conn.close()
        return {
            "success": False,
            "error": "Rate limit exceeded. Maximum 10 reports per device per hour allowed."
        }

    # 2. Deduplication Check: Same device reporting same indicator in past 24 hours
    day_ago = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        SELECT id FROM reports 
        WHERE device_hash = ? AND indicator_hash = ? AND created_at >= ?
    """, (device_hash, indicator_hash, day_ago))
    duplicate = cursor.fetchone()

    if duplicate:
        conn.close()
        return {
            "success": True,
            "deduplicated": True,
            "message": "Report already recorded for this device today."
        }

    # 3. Insert Report
    cursor.execute("""
        INSERT INTO reports (scam_type, district, indicator_hash, indicator_raw, device_hash)
        VALUES (?, ?, ?, ?, ?)
    """, (scam_type, district, indicator_hash, indicator_clean, device_hash))

    # 4. Update Indicator Confirmation Status
    cursor.execute("SELECT * FROM indicators WHERE indicator_hash = ?", (indicator_hash,))
    existing_indicator = cursor.fetchone()

    # Count distinct devices that have reported this indicator
    cursor.execute("""
        SELECT COUNT(DISTINCT device_hash) as dev_cnt 
        FROM reports 
        WHERE indicator_hash = ?
    """, (indicator_hash,))
    distinct_devices = cursor.fetchone()["dev_cnt"]

    is_confirmed = distinct_devices >= confirmation_n
    status = "Confirmed" if is_confirmed else "Unconfirmed"
    confirmed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if is_confirmed else None

    if existing_indicator:
        cursor.execute("""
            UPDATE indicators 
            SET distinct_device_count = ?, status = ?, confirmed_at = COALESCE(confirmed_at, ?)
            WHERE indicator_hash = ?
        """, (distinct_devices, status, confirmed_at, indicator_hash))
    else:
        cursor.execute("""
            INSERT INTO indicators (indicator_hash, indicator_raw, scam_type, status, distinct_device_count, confirmed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (indicator_hash, indicator_clean, scam_type, status, distinct_devices, confirmed_at))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "indicator_hash": indicator_hash,
        "status": status,
        "distinct_devices": distinct_devices,
        "needed_for_confirmation": confirmation_n,
        "confirmed": is_confirmed
    }
