"""
Rule Engine for Suraksha Fraud Detection
Multi-lingual rules (English, Hindi, Hinglish) with Genuine Bank Safety Guards.
"""

import re

# Genuine OTP alert guard phrases (banks explicitly warning the customer NOT to share)
GENUINE_SAFETY_PATTERNS = [
    r"do\s+not\s+share\s+(?:this\s+)?(?:otp|code|password)\b",
    r"never\s+share\s+(?:your\s+)?(?:otp|pin|password)\b",
    r"bank\s+never\s+(?:calls\s+to\s+)?asks?\s+(?:for\s+)?otp\b",
    r"kisi\s+(?:ko|ke\s+saath)\s+share\s+na\s+kare[mn]?\b",
    r"kisi\s+ko\s+na\s+bataye[mn]?\b",
    r"साझा\s+न\s+करें",
    r"किसी\s+को\s+न\s+बताएं",
    r"ओटीपी\s+साझा\s+न\s+करें",
    r"बैंक\s+कभी\s+भी\s+otp\s+नहीं\s+पूछता",
    r"ककरो\s+ले\s+झन\s+बताव",
    r"ककरो\s+ले\s+शेयर\s+झन\s+करव"
]

# Fraudulent OTP demands (demanding customer send or tell the OTP to someone)
FRAUDULENT_OTP_PATTERNS = [
    r"(?:share|send|tell|give|enter)\s+(?:your\s+)?(?:6\s*[-]?\s*digit\s+)?(?:otp|pin|cvv|password)\s+(?:to|with|on)\b",
    r"otp\s+(?:batao|bataiye|send\s+karo|share\s+kare|dijiye)\b",
    r"ओटीपी\s*(?:बताएं|दीजिए|भेजें|दर्ज\s+करें)\b",
    r"otp\s+(?:बताव|डारव|भेजव)\b",
    r"share\s+your\s+debit\s+card\s+cvv\b",
    r"card\s+ka\s+cvv\s+aur\s+otp\b"
]

# Digital Arrest & Extortion
DIGITAL_ARREST_PATTERNS = [
    r"digital\s+arrest\b",
    r"डिजिटल\s+अरेस्ट\b",
    r"stay\s+on\s+(?:the\s+)?(?:video\s+)?call\b",
    r"do\s+not\s+(?:disconnect|cut)\s+(?:this\s+)?call\b",
    r"call\s+cut\s+mat\s+karna\b",
    r"phone\s+mat\s+katna\b",
    r"do\s+not\s+tell\s+anyone\b",
    r"kisi\s+ko\s+mat\s+batana\b",
    r"drugs\s+(?:and\s+passports?\s+)?in\s+(?:your\s+)?parcel\b",
    r"narkotiks|contraband|nashi?li\s+dawa\b",
    r"(?:mumbai|delhi)?\s*(?:police|crime\s+branch|cbi|customs)\s+(?:notice|warrant|interrogat)\b",
    r"जमानत\s+राशि|clearance\s+bond\b"
]

# Fake KYC and Account Suspend Threats
FAKE_KYC_PATTERNS = [
    r"(?:account|a/c|yono|sim|debit\s+card)\s+(?:is\s+)?(?:suspended|blocked|deactivated|closed|sealed)\b",
    r"खाता\s+(?:बंद|ब्लॉक|सील)\s+हो\s+गया\b",
    r"account\s+block\s+ho\s+gaya\b",
    r"update\s+(?:your\s+)?kyc\s+immediately\b",
    r"kyc\s+update\s+kar(?:e|o)\b",
    r"केवाईसी\s+(?:अपडेट|सत्यापन)\b",
    r"electricity\s+(?:power\s+)?will\s+be\s+disconnected\s+tonight\b",
    r"bijli\s+kaat\s+di\s+jayegi\b",
    r"बिजली\s+काट\s+दी\s+जाएगी\b",
    r"cspdcl\s+electricity\s+officer\b"
]

# Remote Access APKs
REMOTE_ACCESS_PATTERNS = [
    r"\b(?:anydesk|quicksupport|rustdesk|teamviewer|zoho\s+assist)\b",
    r"एनीडेस्क|क्विक\s*सपोर्ट\b",
    r"install\s+apk|download\s+apk\b"
]

# Suspicious Link Patterns
SUSPICIOUS_LINK_PATTERNS = [
    r"\b(?:bit\.ly|tinyurl\.com|is\.gd|cutt\.ly|t\.co)/\S+",
    r"\b\w+[-_](?:kyc|sbi|yono|cspdcl|police|customs)\.(?:top|vip|xyz|cc|site|live|online|in)\b",
    r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
    r"\b[a-zA-Z0-9.-]+\.apk\b"
]

# Urgency and Pressure Tactics
URGENCY_PATTERNS = [
    r"\b(?:immediately|urgent(?:ly)?|within\s+2\s+hours?|tonight\s+at\s+9:30|before\s+deadline)\b",
    r"\b(?:turant|aaj\s+raat|jaldi|aaj\s+hi|2\s+ghante\s+me)\b",
    r"तुरंत|आज\s+रात|2\s+घंटे\s+में|जल्दी\b",
    r"तुरते|आज\s+संझा\b"
]

def check_rules(text: str) -> dict:
    text_lower = text.lower()
    matches = []
    rule_flags = {
        "is_genuine_alert": False,
        "explicit_otp_demand": False,
        "digital_arrest": False,
        "fake_kyc": False,
        "remote_access_apk": False,
        "suspicious_link": False,
        "urgency_pressure": False
    }

    # Check genuine bank guard first
    for pat in GENUINE_SAFETY_PATTERNS:
        found = re.findall(pat, text_lower, flags=re.IGNORECASE)
        if found:
            rule_flags["is_genuine_alert"] = True
            matches.append({"rule": "genuine_safety_notice", "phrase": found[0], "risk": False})

    # Fraudulent OTP request
    for pat in FRAUDULENT_OTP_PATTERNS:
        found = re.findall(pat, text_lower, flags=re.IGNORECASE)
        if found:
            rule_flags["explicit_otp_demand"] = True
            matches.append({"rule": "fraudulent_otp_demand", "phrase": found[0], "risk": True})

    # Digital Arrest
    for pat in DIGITAL_ARREST_PATTERNS:
        found = re.findall(pat, text_lower, flags=re.IGNORECASE)
        if found:
            rule_flags["digital_arrest"] = True
            matches.append({"rule": "digital_arrest_extortion", "phrase": found[0], "risk": True})

    # Fake KYC & Power Cut threats
    for pat in FAKE_KYC_PATTERNS:
        found = re.findall(pat, text_lower, flags=re.IGNORECASE)
        if found:
            rule_flags["fake_kyc"] = True
            matches.append({"rule": "fake_kyc_threat", "phrase": found[0], "risk": True})

    # Remote Access Apps
    for pat in REMOTE_ACCESS_PATTERNS:
        found = re.findall(pat, text_lower, flags=re.IGNORECASE)
        if found:
            rule_flags["remote_access_apk"] = True
            matches.append({"rule": "remote_access_app", "phrase": found[0], "risk": True})

    # Suspicious Links
    for pat in SUSPICIOUS_LINK_PATTERNS:
        found = re.findall(pat, text_lower, flags=re.IGNORECASE)
        if found:
            rule_flags["suspicious_link"] = True
            matches.append({"rule": "suspicious_link", "phrase": found[0], "risk": True})

    # Urgency & Panic
    for pat in URGENCY_PATTERNS:
        found = re.findall(pat, text_lower, flags=re.IGNORECASE)
        if found:
            rule_flags["urgency_pressure"] = True
            matches.append({"rule": "urgency_panic", "phrase": found[0], "risk": True})

    # Compute rule-based risk score (0 to 1)
    risk_score = 0.0
    if rule_flags["explicit_otp_demand"]:
        risk_score += 0.8
    if rule_flags["digital_arrest"]:
        risk_score += 0.8
    if rule_flags["fake_kyc"]:
        risk_score += 0.5
    if rule_flags["remote_access_apk"]:
        risk_score += 0.6
    if rule_flags["suspicious_link"]:
        risk_score += 0.5
    if rule_flags["urgency_pressure"]:
        risk_score += 0.3

    risk_score = min(risk_score, 1.0)

    # Genuine guard override: If genuine alert matches and NO explicit OTP demands
    if rule_flags["is_genuine_alert"] and not rule_flags["explicit_otp_demand"]:
        risk_score = 0.0

    return {
        "flags": rule_flags,
        "matches": matches,
        "rule_risk_score": risk_score
    }
