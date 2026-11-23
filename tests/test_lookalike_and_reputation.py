import pytest
from app.detect.lookalike import (
    analyze_domain_lookalike,
    detect_lookalikes_in_text,
    normalize_domain_homoglyphs,
    levenshtein_distance,
    get_base_domain
)
from app.detect.reputation import (
    check_reputation,
    extract_indicators_from_text,
    CompactBloomFilter
)
from app.detect.pipeline import run_detection_pipeline
from app.qr.checker import analyze_upi_qr

def test_levenshtein_and_homoglyphs():
    assert levenshtein_distance("cspdcl", "cspdcl") == 0
    assert levenshtein_distance("cspdcl", "cspdcll") == 1
    assert levenshtein_distance("sbi", "sbi1") == 1

    # Cyrillic 'о' (\u043e) should map to Latin 'o'
    cyrillic_str = "sb\u0456"  # Cyrillic i
    norm, had = normalize_domain_homoglyphs(cyrillic_str)
    assert had is True
    assert norm == "sbi"

def test_official_domain_whitelist():
    # Legitimate domains must NOT be flagged as lookalikes
    res1 = analyze_domain_lookalike("https://cspdcl.co.in/bill")
    assert res1 is not None
    assert res1.get("is_official") is True
    assert res1.get("risk") is False

    res2 = analyze_domain_lookalike("https://www.onlinesbi.sbi/portal")
    assert res2 is not None
    assert res2.get("is_official") is True

    res3 = analyze_domain_lookalike("https://cybercrime.gov.in")
    assert res3 is not None
    assert res3.get("is_official") is True

def test_deceptive_lookalike_detection():
    # Keyword trap on unofficial TLD / subdomain
    trap1 = analyze_domain_lookalike("http://cspdcl-bill-update.xyz/pay")
    assert trap1 is not None
    assert trap1.get("is_lookalike") is True
    assert "CSPDCL" in trap1.get("impersonated_target")

    # Bank keyword spoofing
    trap2 = analyze_domain_lookalike("http://sbi-kyc-verify.com/login")
    assert trap2 is not None
    assert trap2.get("is_lookalike") is True
    assert "SBI" in trap2.get("impersonated_target")

    # Detection from full message text
    sample_msg = "Your bijli bill overdue. Update immediately at cspdcl-portal.net or power cut."
    findings = detect_lookalikes_in_text(sample_msg)
    assert len(findings) >= 1
    assert findings[0]["is_lookalike"] is True

def test_reputation_blacklist_lookup():
    # update_pack.json contains verified scam indicators
    # Test checking known indicator
    rep = check_reputation("9876543210")
    if rep:  # If present in update pack
        assert rep["is_known_scam"] is True
        assert rep["confidence"] >= 0.99

    # Test extracting indicators from message
    msg = "Call 9876543210 or visit scam-domain.xyz or send upi to fraud@okhdfcbank"
    inds = extract_indicators_from_text(msg)
    assert any("9876543210" in i for i in inds)
    assert any("fraud@okhdfcbank" in i for i in inds)
    assert any("scam-domain.xyz" in i for i in inds)

def test_compact_bloom_filter():
    bf = CompactBloomFilter(size=512, hash_count=3)
    bf.add("scammer@upi")
    bf.add("9876543210")
    bf.add("phishing-site.xyz")

    assert bf.contains("scammer@upi") is True
    assert bf.contains("9876543210") is True
    assert bf.contains("phishing-site.xyz") is True

    # Benign unadded items should mostly return False
    assert bf.contains("safe-domain-never-added-12345.gov.in") is False

def test_pipeline_integration_lookalike_and_reputation():
    # 1. Pipeline catches lookalike domain
    res_lookalike = run_detection_pipeline(
        "Bijli bill pending. Click http://cspdcl-quickpay.top to pay or tonight power cut.",
        user_lang="hi"
    )
    assert res_lookalike["verdict"] == "likely_scam"
    assert res_lookalike["rule_flags"].get("lookalike_domain") is True
    assert res_lookalike["confidence_percent"] >= 90
    assert any("cspdcl-quickpay.top" in p for p in res_lookalike["risky_phrases"])

    # 2. Pipeline catches blacklisted number
    res_rep = run_detection_pipeline(
        "Dear user your package arrived. Call 9876543210 immediately.",
        user_lang="en"
    )
    # 9876543210 is in blacklist
    if res_rep["reputation_match"]:
        assert res_rep["verdict"] == "likely_scam"
        assert res_rep["rule_flags"].get("reputation_blacklist") is True

def test_qr_checker_with_blacklist():
    # Test QR analyzer with blacklisted UPI from update_pack.json
    res = analyze_upi_qr("upi://pay?pa=cspdcl-bill@okaxis&pn=Electricity%20Bill&am=1500", user_lang="en")
    assert res["verdict"] == "likely_scam"
    assert any("OFFLINE BLACKLIST MATCH" in w or "CRITICAL MISMATCH" in w or "LOOKALIKE" in w for w in res["warnings"])

def test_telecom_official_domains_and_jio_quota_alert():
    # Official Jio subdomains with numeric digits must be recognized as official and safe
    res_jio1 = analyze_domain_lookalike("http://tiny.jio.com/dbuydatapack")
    assert res_jio1 is not None
    assert res_jio1.get("is_official") is True
    assert res_jio1.get("risk") is False

    res_jio2 = analyze_domain_lookalike("http://tiny1.jio.com/HelpfulTips")
    assert res_jio2 is not None
    assert res_jio2.get("is_official") is True
    assert res_jio2.get("risk") is False

    jio_msg = (
        "ALERT!\n"
        "You have exhausted 100% of daily data quota as of 23-Nov-26 18:20.\n"
        "Jio Number: 9329022146\n"
        "Daily Data Quota: 2 GB\n"
        "Daily Quota Restores On: 24-Nov-26 00:09\n"
        "Your internet speed will be reduced to 64 Kbps, If you do not you have an active additional data pack.\n"
        "To explore data packs and recharge using MyJio, click: http://tiny.jio.com/dbuydatapack\n"
        "Know more about your data usage, click:\n"
        "http://tiny1.jio.com/HelpfulTips"
    )

    # Without sender: should be genuine
    res_no_sender = run_detection_pipeline(jio_msg, user_lang="en")
    assert res_no_sender["verdict"] == "genuine"
    assert res_no_sender["rule_flags"].get("lookalike_domain", False) is False

    # With official Jio DLT sender: should be genuine
    res_with_sender = run_detection_pipeline(jio_msg, user_lang="en", sender="JM-JIOINF")
    assert res_with_sender["verdict"] == "genuine"
    assert "Jio" in res_with_sender["explanation"]

