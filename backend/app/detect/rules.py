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
    r"kisi\s+ko\s+(?:bhi\s+)?(?:na|mat)\s+bataye[mn]?\b",
    r"bank\s+kabhi\s+(?:bhi\s+)?otp\s+nahi\s+mangta\b",
    r"साझा\s+न\s+करें",
    r"किसी\s+को\s+न\s+बताएं",
    r"ओटीपी\s+साझा\s+न\s+करें",
    r"बैंक\s+कभी\s+भी\s+otp\s+नहीं\s+पूछता",
    r"ककरो\s+ले\s+(?:शेयर\s+)?झन\s+बताव",
    r"ककरो\s+ले\s+साझा\s+झन\s+करव",
    r"बैंक\s+कभू\s+(?:घलो\s+)?otp\s+नइ\s+मांगय",
    r"kakar\s+sang\s+jhan\s+share\s+karaw\b"
]

# Fraudulent OTP demands (demanding customer send or tell the OTP to someone)
FRAUDULENT_OTP_PATTERNS = [
    r"(?:share|send|tell|give|enter)\s+(?:your\s+)?(?:6\s*[-]?\s*digit\s+)?(?:otp|pin|cvv|password)\s+(?:to|with|on)\b",
    r"otp\s+(?:batao|bataiye|send\s+karo|share\s+kare|dijiye|forward\s+kare)\b",
    r"apna\s+(?:6\s*[-]?\s*digit\s+)?(?:otp|pin|cvv)\s+batao\b",
    r"ओटीपी\s*(?:बताएं|दीजिए|भेजें|दर्ज\s+करें)",
    r"मोबाइल\s+म\s+आए\s+otp\s+ल\s+बताव",
    r"ओटीपी\s*(?:बताव|डारव|भेजव)",
    r"otp\s+(?:बताव|डारव|भेजव|la\s+bataw|daraw|bhejaw)",
    r"share\s+your\s+debit\s+card\s+cvv\b",
    r"card\s+ka\s+cvv\s+aur\s+otp\b"
]

# Digital Arrest & Extortion (English, Hindi, Hinglish, Chhattisgarhi)
DIGITAL_ARREST_PATTERNS = [
    r"digital\s+arrest\b",
    r"डिजिटल\s+अरेस्ट",
    r"stay\s+on\s+(?:the\s+)?(?:video\s+)?call\b",
    r"do\s+not\s+(?:disconnect|cut)\s+(?:this\s+)?call\b",
    r"call\s+(?:cut|disconnect)\s+mat\s+karna\b",
    r"video\s+call\s+(?:pe|par)\s+(?:bane\s+raho|raho)\b",
    r"phone\s+mat\s+katna\b",
    r"do\s+not\s+tell\s+anyone\b",
    r"kisi\s+ko\s+mat\s+batana\b",
    r"drugs\s+(?:and\s+passports?\s+)?in\s+(?:your\s+)?parcel\b",
    r"parcel\s+me\s+(?:drugs|narcotics|passports?)\s+mila\b",
    r"narkotiks|contraband|nashi?li\s+dawa\b",
    r"(?:mumbai|delhi)?\s*(?:police|crime\s+branch|cbi|customs)\s+(?:notice|warrant|interrogat|se\s+bol\s+raha)\b",
    r"arrest\s+warrant\s+(?:issue|nikla|jari)\s+hua\b",
    r"bail\s+(?:security\s+)?bond\s+(?:transfer\s+karo|bhejo)\b",
    r"जमानत\s+राशि|clearance\s+bond",
    # Chhattisgarhi forms
    r"थाना\s+ले\s+बोलत\s+हंव",
    r"तोर\s+नाम\s+म\s+वारंट",
    r"कॉल\s+ल\s+झन\s+काटव",
    r"वीडियो\s+कॉल\s+म\s+बने\s+रहव",
    r"पईसा\s+जमा\s+करव\s+नइ\s+ते\s+जेल",
    r"तोर\s+पार्सल\s+म\s+(?:चरस|गांजा|ड्रग्स)",
    r"thana\s+le\s+bolat\s+hanw\b",
    r"tor\s+naam\s+ma\s+warrant\b",
    r"call\s+la\s+jhan\s+kataw\b"
]

# Fake KYC and Account Suspend Threats (English, Hindi, Hinglish, Chhattisgarhi)
FAKE_KYC_PATTERNS = [
    r"(?:account|a/c|yono|sim|debit\s+card)\s+(?:is\s+)?(?:suspended|blocked|deactivated|closed|sealed)\b",
    r"खाता\s+(?:बंद|ब्लॉक|सील)\s+हो\s+गया",
    r"account\s+(?:block|freeze|suspend)\s+ho\s+gaya\b",
    r"update\s+(?:your\s+)?kyc\s+immediately\b",
    r"kyc\s+update\s+kar(?:e|o)\b",
    r"केवाईसी\s+(?:अपडेट|सत्यापन)",
    r"electricity\s+(?:power\s+)?will\s+be\s+disconnected\s+tonight\b",
    r"bijli\s+(?:line|connection)\s+(?:aaj\s+raat\s+)?(?:kaat\s+di\s+jayegi|kat\s+jayega|cut\s+ho\s+jayega)\b",
    r"बिजली\s+(?:काट\s+दी\s+जाएगी|बिल\s+(?:न[इी]|नहीं)\s+भरे|लाइन\s+कट\s*जाही)",
    r"लाइन\s+कट\s*जाही",
    r"cspdcl\s+electricity\s+officer\b",
    # Chhattisgarhi forms
    r"तोर\s+(?:बिजली|लाइन)\s+कट\s*जाही",
    r"तोर\s+बिजली",
    r"बिल\s+(?:न[इी]|नहीं)\s+भरे",
    r"बिल\s+तुरते\s+पटाव",
    r"तोर\s+(?:बैंक\s+)?खाता\s+(?:बंद|सील|ब्लॉक)",
    r"tor\s+bijli\s+line\s+kat\s*jahi\b",
    r"bill\s+nai\s+bhare\s+has\b",
    r"bill\s+turte\s+pataw\b",
    r"tor\s+khata\s+band\s+howat\s+he\b"
]

# Remote Access APKs
REMOTE_ACCESS_PATTERNS = [
    r"\b(?:anydesk|quicksupport|rustdesk|teamviewer|zoho\s+assist)\b",
    r"एनीडेस्क|क्विक\s*सपोर्ट\b",
    r"install\s+apk|download\s+apk\b",
    r"apk\s+(?:download|install)\s+kar(?:e|o|aw)\b",
    r"screen\s+share\s+kar(?:e|o)\b"
]

# Suspicious Link Patterns
SUSPICIOUS_LINK_PATTERNS = [
    r"\b(?:bit\.ly|tinyurl\.com|is\.gd|cutt\.ly|t\.co)/\S+",
    r"\b\w+[-_](?:kyc|sbi|yono|cspdcl|police|customs)\.(?:top|vip|xyz|cc|site|live|online|in)\b",
    r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
    r"\b[a-zA-Z0-9.-]+\.apk\b"
]

# Urgency and Pressure Tactics (English, Hindi, Hinglish, Chhattisgarhi)
URGENCY_PATTERNS = [
    r"\b(?:immediately|urgent(?:ly)?|within\s+2\s+hours?|tonight\s+at\s+9:30|before\s+deadline)\b",
    r"\b(?:turant|aaj\s+raat|jaldi|aaj\s+hi|2\s+ghante\s+me|jald\s+se\s+jald)\b",
    r"तुरंत|आज\s+रात|2\s+घंटे\s+में|जल्दी",
    r"तुरते|आज\s+संझा|झन\s+देरी\s+करव|2\s+घंटा\s+म",
    r"\b(?:turte|aaj\s+sanjha|jhan\s+deri\s+karaw)\b"
]

def check_rules(text: str, raw_text: str = None) -> dict:
    target_texts = [text.lower()]
    if raw_text and raw_text.lower() not in target_texts:
        target_texts.append(raw_text.lower())

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

    def find_in_targets(pattern):
        for target in target_texts:
            res = re.findall(pattern, target, flags=re.IGNORECASE)
            if res:
                return res
        return []

    # Check genuine bank guard first
    for pat in GENUINE_SAFETY_PATTERNS:
        found = find_in_targets(pat)
        if found:
            rule_flags["is_genuine_alert"] = True
            matches.append({"rule": "genuine_safety_notice", "phrase": found[0], "risk": False})

    # Fraudulent OTP request
    for pat in FRAUDULENT_OTP_PATTERNS:
        found = find_in_targets(pat)
        if found:
            rule_flags["explicit_otp_demand"] = True
            matches.append({"rule": "fraudulent_otp_demand", "phrase": found[0], "risk": True})

    # Digital Arrest
    for pat in DIGITAL_ARREST_PATTERNS:
        found = find_in_targets(pat)
        if found:
            rule_flags["digital_arrest"] = True
            matches.append({"rule": "digital_arrest_extortion", "phrase": found[0], "risk": True})

    # Fake KYC & Power Cut threats
    for pat in FAKE_KYC_PATTERNS:
        found = find_in_targets(pat)
        if found:
            rule_flags["fake_kyc"] = True
            matches.append({"rule": "fake_kyc_threat", "phrase": found[0], "risk": True})

    # Remote Access Apps
    for pat in REMOTE_ACCESS_PATTERNS:
        found = find_in_targets(pat)
        if found:
            rule_flags["remote_access_apk"] = True
            matches.append({"rule": "remote_access_app", "phrase": found[0], "risk": True})

    # Suspicious Links
    for pat in SUSPICIOUS_LINK_PATTERNS:
        found = find_in_targets(pat)
        if found:
            rule_flags["suspicious_link"] = True
            matches.append({"rule": "suspicious_link", "phrase": found[0], "risk": True})

    # Urgency & Panic
    for pat in URGENCY_PATTERNS:
        found = find_in_targets(pat)
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
