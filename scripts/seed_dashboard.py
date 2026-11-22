"""
Seed Script for Suraksha Dashboard Demo Data
Populates realistic confirmed and unconfirmed reports across Chhattisgarh districts:
Raipur, Durg, Bilaspur, Korba, Raigarh, Bastar, Rajnandgaon, Surguja.
Respects multi-device confirmation logic (N=3) so some indicators are Confirmed and others Unconfirmed.
"""

import sys
from pathlib import Path
import random

workspace_dir = Path(__file__).resolve().parent.parent
backend_dir = workspace_dir / "backend"
sys.path.insert(0, str(backend_dir))

from app.reports.database import init_db, get_connection
from app.reports.service import submit_anonymous_report
from app.dashboard.alerts import cluster_emerging_reports

DISTRICTS = [
    "Raipur", "Durg", "Bilaspur", "Korba", "Raigarh", "Bastar", "Rajnandgaon", "Surguja"
]

SCAM_TYPES = [
    ("Electricity Bill", ["cspdcl-pay.top", "9827104921", "9876543210", "cspdcl-bill.xyz"]),
    ("Digital Arrest", ["cbi-clearance-desk", "919820011223", "mumbai-cyber-arrest.in"]),
    ("Fake KYC", ["sbi-yono-update.vip", "9425201928", "anydesk-support-desk"]),
    ("Fake QR", ["electricity@okhdfc", "police-fine@paytm", "cspdcl-bill@okaxis"]),
    ("Loan App", ["instant-cash-chhattisgarh.apk", "fast-rupee-loan.in"]),
    ("Courier Scam", ["fedex-customs-parcel.cc", "9981203948"]),
    ("OTP Request", ["9826102938", "sbi-otp-verification", "9406102931"])
]

def seed_demo_data():
    print("🌱 Seeding realistic dashboard demo data for Chhattisgarh districts...")
    init_db()

    random.seed(108)

    # 1. Seed Confirmed Indicators (reported by 3 to 6 distinct devices)
    for scam_type, indicators in SCAM_TYPES:
        for ind in indicators:
            district = random.choice(DISTRICTS)
            device_count = random.randint(3, 7)  # will reach >= 3 confirmation
            for dev_idx in range(device_count):
                device_id = f"dev_{scam_type[:3]}_{ind[:4]}_{dev_idx}_{random.randint(100, 999)}"
                submit_anonymous_report(
                    scam_type=scam_type,
                    district=district,
                    raw_indicator=ind,
                    raw_device_id=device_id,
                    confirmation_n=3
                )

    # 2. Seed some Unconfirmed Indicators (reported by only 1 or 2 devices)
    unconfirmed_indicators = [
        ("Loan App", "Korba", "new-quick-loan-app.apk"),
        ("OTP Request", "Bastar", "9406001122"),
        ("Fake QR", "Surguja", "test-personal@ybl"),
        ("Fake KYC", "Raigarh", "bank-update-link.site")
    ]
    for scam_type, district, ind in unconfirmed_indicators:
        submit_anonymous_report(
            scam_type=scam_type,
            district=district,
            raw_indicator=ind,
            raw_device_id=f"single_user_{random.randint(1000, 9999)}",
            confirmation_n=3
        )

    # 3. Trigger emerging scam clusters
    cluster_emerging_reports(min_cluster_size=3)

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM reports")
    rep_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM indicators WHERE status = 'Confirmed'")
    conf_cnt = c.fetchone()[0]
    conn.close()

    print(f"✅ Seeding complete! Total Reports: {rep_cnt}, Confirmed Blacklist Indicators: {conf_cnt}")

if __name__ == "__main__":
    seed_demo_data()
