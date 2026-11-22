"""
Policy Dashboard Analytics for District Administration & Banks
- Only includes CONFIRMED reports
- Suppresses counts below k=5 for privacy protection
- Filters by district and time window
"""

from datetime import datetime, timedelta, timezone
from app.reports.database import get_connection

PRIVACY_K_MIN = 5

CHHATTISGARH_DISTRICTS = [
    "Raipur", "Durg", "Bilaspur", "Korba", "Raigarh", "Bastar", "Rajnandgaon", "Surguja"
]

SCAM_CATEGORIES = [
    "OTP Request", "Fake QR", "Loan App", "Scam Call", "Fake KYC", "Digital Arrest", "Courier Scam"
]

def get_dashboard_metrics(district: str = "ALL", time_filter: str = "all") -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    # Time clause
    time_clause = ""
    time_params = []
    if time_filter == "7d":
        since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        time_clause = "AND r.created_at >= ?"
        time_params.append(since)
    elif time_filter == "30d":
        since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        time_clause = "AND r.created_at >= ?"
        time_params.append(since)

    district_clause = ""
    dist_params = []
    if district and district.upper() != "ALL":
        district_clause = "AND r.district = ?"
        dist_params.append(district)

    query_params = dist_params + time_params

    # 1. Total Confirmed Reports Count
    cursor.execute(f"""
        SELECT COUNT(r.id) as cnt
        FROM reports r
        JOIN indicators i ON r.indicator_hash = i.indicator_hash
        WHERE i.status = 'Confirmed' {district_clause} {time_clause}
    """, query_params)
    total_confirmed = cursor.fetchone()["cnt"]

    # 2. Total Raw Reports Count (for transparency)
    cursor.execute(f"""
        SELECT COUNT(r.id) as cnt
        FROM reports r
        WHERE 1=1 {district_clause} {time_clause}
    """, query_params)
    total_reports = cursor.fetchone()["cnt"]

    # 3. Breakdown by Scam Type (Confirmed Only, k >= 5 rule)
    cursor.execute(f"""
        SELECT r.scam_type, COUNT(r.id) as cnt
        FROM reports r
        JOIN indicators i ON r.indicator_hash = i.indicator_hash
        WHERE i.status = 'Confirmed' {district_clause} {time_clause}
        GROUP BY r.scam_type
        ORDER BY cnt DESC
    """, query_params)
    raw_by_type = {row["scam_type"]: row["cnt"] for row in cursor.fetchall()}

    by_scam_type = []
    for cat in SCAM_CATEGORIES:
        count = raw_by_type.get(cat, 0)
        # Privacy suppression
        suppressed = (0 < count < PRIVACY_K_MIN)
        display_val = "< 5" if suppressed else count
        by_scam_type.append({
            "category": cat,
            "count": 0 if suppressed else count,
            "display": display_val,
            "suppressed": suppressed
        })

    # 4. Breakdown by District (Confirmed Only, k >= 5 rule)
    cursor.execute(f"""
        SELECT r.district, COUNT(r.id) as cnt
        FROM reports r
        JOIN indicators i ON r.indicator_hash = i.indicator_hash
        WHERE i.status = 'Confirmed' {time_clause}
        GROUP BY r.district
        ORDER BY cnt DESC
    """, time_params)
    raw_by_dist = {row["district"]: row["cnt"] for row in cursor.fetchall()}

    by_district = []
    for d in CHHATTISGARH_DISTRICTS:
        count = raw_by_dist.get(d, 0)
        suppressed = (0 < count < PRIVACY_K_MIN)
        display_val = "< 5" if suppressed else count
        by_district.append({
            "district": d,
            "count": 0 if suppressed else count,
            "display": display_val,
            "suppressed": suppressed
        })

    # Active clusters / alerts count
    cursor.execute("SELECT COUNT(*) as alert_cnt FROM scam_clusters")
    alert_count = cursor.fetchone()["alert_cnt"]

    conn.close()

    return {
        "filter": {"district": district, "time": time_filter},
        "k_suppression_threshold": PRIVACY_K_MIN,
        "total_confirmed_reports": total_confirmed,
        "total_submitted_reports": total_reports,
        "active_alerts_count": alert_count,
        "by_scam_type": by_scam_type,
        "by_district": by_district
    }
