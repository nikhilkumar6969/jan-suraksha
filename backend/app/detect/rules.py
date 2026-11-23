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
    r"ककरो\s+ले\s+.*?(?:झन\s+बताव|झन\s+बतावव|साझा\s+झन\s+करव)",
    r"ककरो\s+ले\s+साझा\s+झन\s+करव",
    r"बैंक\s+कभू\s+(?:फोन\s+म\s+)?(?:घलो\s+)?(?:otp|ओटीपी|पिन)\s+नइ\s+मांगय",
    r"kakar\s+sang\s+jhan\s+share\s+karaw\b",
    # Hard negative protections: genuine bank advisories, visit branch, maintenance, government notices
    r"bank\s+advisory\b",
    r"बैंक\s+सूचना|आवश्यक\s+बैंक\s+सूचना",
    r"(?:app\s+)?(?:download|install)\s+(?:na|mat)\s+kare[mn]?\b",
    r"screen\s+share\s+(?:na\s+kare|nahi\s+mangta|mat\s+kare|न\s+करें)\b",
    r"do\s+not\s+(?:download|install|share\s+screen)\b",
    r"visit\s+(?:your\s+)?(?:home\s+)?branch\b",
    r"शाखा\s+म[ेंा]\s+जाके|शाखा\s+में\s+जाकर",
    r"scheduled\s+maintenance\b",
    r"संधारण\s+कार्य|मरम्मत\s+कार्य|सबस्टेशन",
    r"school\s+bus\s+fees|स्कूल\s+बस\s+फीस",
    r"petrol\s+pump\s+par\s+khada\b|पेट्रोल\s+पंप",
    r"library\s+books|पुस्तकालय",
    r"police\s+station\s+gate|थाने\s+के\s+सामने|थाना\s+चौक",
    r"order\s+(?:with\s+tracking\s+)?(?:[a-z0-9]+\s+)?(?:is\s+out\s+for|will\s+be)\s+delivery|पार्सल\s+.*?आज\s+डिलीवर|delivery\s+agent",
    r"धान\s+परिवहन|टोकन|राशन\s+दुकान|चांउर|सोसाइटी\s+म\s+संपर्क|पासबुक\s+म\s+इंदराज",
    r"power\s+line\s+maintenance|लाइन\s+रखरखाव",
    r"सार्वजनिक\s+अवकाश|public\s+holiday",
    # User narration & benign personal finance statements
    r"\b(?:maine|humne|i\s+have|i\s+already)\s+(?:entered|dala|bhara|diya|paid|pay\s+kar\s+diya|transferred)\b",
    r"मैंने\s+(?:अपना\s+)?(?:otp|पिन|बिल|पैसे|रुपये|राशि)\s+(?:डाल\s+दिया|भर\s+दिया|दे\s+दिया|ट्रांसफर\s+कर\s+दिए)",
    r"मंय\s+(?:अपन\s+)?(?:बिल|प[ईइ]सा|रुपिया)\s+पटा\s+दे\s+हंव",
    r"मंय\s+(?:अपन\s+)?हाथ\s+ले\s+बिल\s+पटाए\s+हंव",
    r"धान\s+के\s+बोनस",
    r"सोसाइटी\s+म\s+धान",
    r"पासबुक\s+चढ़ाए\s+बर",
    r"पासबुक\s+में\s+एंट्री",
    r"प[ईइ]सा\s+निकाले\s+बर\s+बैंक\s+शाखा"
]

# Fraudulent OTP & UPI PIN demands
FRAUDULENT_OTP_PATTERNS = [
    r"(?:share|send|tell|give|enter|forward|put|type)\s+(?:the\s+)?(?:your\s+)?(?:google\s+pay\s+|gpay\s+|phonepe\s+|paytm\s+|bank\s+)?(?:6\s*[-]?\s*digit\s+)?(?:upi\s+)?(?:otp|pin|cvv|code|password|confirmation\s+code|verification\s+code)\b",
    r"\benter\s+(?:your\s+)?(?:upi\s+)?pin\s+to\s+(?:receive|accept|get|credit)\s+(?:money|cashback|payment|rupees)\b",
    r"\b(?:upi\s+)?pin\s+(?:dalo|batao|share\s+kare|daraw|bataw)\b",
    r"otp\s+(?:batao|bataiye|send\s+karo|share\s+kare|dijiye|forward\s+kare|forward|bataye)\b",
    r"apna\s+(?:6\s*[-]?\s*digit\s+)?(?:upi\s+)?(?:otp|pin|cvv)\s+batao\b",
    r"पैसे\s+पाने\s+के\s+लिए\s+(?:अपना\s+)?(?:upi\s+)?पिन\s*(?:डालें|दर्ज\s+करें|लगाएं)",
    r"(?:अपना\s+)?(?:6\s*अंकों\s+का\s+)?(?:गुप्त\s+)?(?:otp|पिन)\s+(?:हमारे\s+)?(?:बैंक\s+)?(?:अधिकारी|एग्जीक्यूटिव|प्रतिनिधि|कस्टमर\s+केयर|नंबर)?\s*(?:को\s+)?(?:बताएं|दीजिए|भेजें|डालें|साझा\s+करें|दर्ज\s+करें)",
    r"ओटीपी\s*(?:बताएं|दीजिए|भेजें|दर्ज\s+करें|साझा\s+करें|बताव|डारव)",
    r"(?:otp|ओटीपी)\s*(?:साझा\s+करें|शेयर\s+करें|बताएं|दीजिए|भेजें|दर्ज\s+करें)",
    r"खाता\s+म\s+प[ईइ]सा\s+आही.*(?:upi\s+)?पिन\s*(?:डारव|बताव|डालव)",
    r"प[ईइ]सा\s+पाए\s+बर.*(?:upi\s+)?पिन\s*(?:डारव|बताव|डालव)",
    r"मोबाइल\s+म\s+आए\s+(?:6\s*अंक\s+के\s+)?(?:otp|कोड)\s+ल\s+(?:बताव|भेजव|डारव)",
    r"(?:otp|ओटीपी|पिन)\s*(?:ला|ल|ओला)?\s*(?:बताव|बतावव|डारव|भेजव)",
    r"otp\s+(?:बताव|डारव|भेजव|la\s+bataw|daraw|bhejaw)",
    r"share\s+your\s+debit\s+card\s+cvv\b",
    r"card\s+ka\s+cvv\s+aur\s+otp\b",
    r"(?:lottery|prize|draw|इनाम|लॉटरी)\s+.*?otp\b"
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
    r"तोर\s+पार्सल\s+म\s+(?:चरस|गांजा|ड्रग्स|नशीली\s+दवा)",
    r"thana\s+le\s+bolat\s+hanw\b",
    r"tor\s+naam\s+ma\s+warrant\b",
    r"call\s+la\s+jhan\s+kataw\b"
]

# Fake KYC and Account Suspend Threats (English, Hindi, Hinglish, Chhattisgarhi)
FAKE_KYC_PATTERNS = [
    r"(?:your\s+)?(?:account|a/c|yono|sim|debit\s+card)\s+.*?(?:suspended|blocked|deactivated|closed|sealed|disabled)\b",
    r"(?:your\s+)?account\s+has\s+been\s+blocked\b",
    r"(?:your\s+)?kyc\s+will\s+expire\b",
    r"kyc\s+(?:समाप्त|एक्सपायर|खत्म)",
    r"(?:बैंक\s+)?खाता\s+.*?(?:बंद|ब्लॉक|सील)\s+(?:हो\s+गया|कर\s+दिया|होवत\s+हे)",
    r"account\s+(?:block|freeze|suspend)\s+ho\s+gaya\b",
    r"update\s+(?:your\s+)?kyc\s+immediately\b",
    r"kyc\s+update\s+kar(?:e|o)\b",
    r"केवाईसी\s+(?:अपडेट|सत्यापन)",
    r"electricity\s+(?:power\s+)?(?:will\s+be\s+disconnected|cutoff)\b",
    r"bijli\s+(?:line|connection)\s+(?:aaj\s+raat\s+)?(?:kaat\s+di\s+jayegi|kat\s+jayega|cut\s+ho\s+jayega)\b",
    r"बिजली\s+(?:काट\s+दी\s+जाएगी|बिल\s+(?:न[इी]|नहीं)\s+भरे|लाइन\s+कट\s*जाही)",
    r"लाइन\s+कट\s*जाही",
    r"cspdcl\s+electricity\s+officer\b",
    r"electricity\s+meter|मीटर\s+म\s+रीडिंग|मीटर\s+में\s+तकनीकी\s+गड़बड़ी",
    r"kbc|lottery|लॉटरी|इनाम\s+मिला|mega\s+draw|cash\s+reward|lucky\s+draw",
    r"रजिस्ट्रेशन\s+फीस|registration\s+fees?|लाइक\s+करके\s+.*?कमा|like\s+videos?\s+.*?earn",
    r"document\s+verification\s+for\s+your\s+recent\s+subsidy|subsidy\s+.*?call\s+back",
    r"data\s+entry\s+operator|part-time\s+work",
    r"yojana\s+form|योजना\s+फार्म\s+.*?विवरण\s+अधूरा|राहत\s+राशि\s+की\s+जांच",
    r"सत्यापन\s+बर\s+फोन\s+करे\s+रिहिसंव|आवास\s+योजना\s+के\s+फार्म",
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

# Remote Access APKs & Tech Support Computer Manipulation
REMOTE_ACCESS_PATTERNS = [
    r"\b(?:anydesk|quicksupport|rustdesk|teamviewer|zoho\s+assist)\b",
    r"एनीडेस्क|क्विक\s*सपोर्ट\b",
    r"\b(?:you\s+need|need\s+a|have\s+a|open|turn\s+on|switch\s+on|start|go\s+to|use)\s+(?:a\s+|your\s+)?(?:computer|pc|laptop|desktop)\b",
    r"\b(?:computer|laptop|pc)\s+(?:on\s+karo|chalu\s+karo|start\s+karo|open\s+karo|me\s+connect)\b",
    r"\b(?:need\s+a\s+computer|access\s+your\s+computer|connect\s+your\s+computer)\b",
    r"कंप्यूटर\s*(?:चालू\s+करो|खोलो|ऑन\s+करो|पे\s+बैठो|में\s+देखो|चाहिए)",
    r"लैपटॉप\s*(?:चालू\s+करो|खोलो|ऑन\s+करो)",
    r"install\s+apk|download\s+apk\b",
    r"apk\s+(?:download|install)\s+kar(?:e|o|aw)\b",
    r"screen\s+share\s+kar(?:e|o)\b"
]

# Suspicious Link Patterns
SUSPICIOUS_LINK_PATTERNS = [
    r"\b(?:click\s+(?:this\s+)?link\s+to\s+(?:verify|update|complete)|verify\s+your\s+account\s+at|update\s+kyc\s+at)\b",
    r"सत्यापन\s+हेतु\s+लिंक|लिंक\s+पर\s+क्लिक\s+करें|लिंक\s+खोल",
    r"\b(?:bit\.ly|tinyurl\.com|is\.gd|cutt\.ly|t\.co)/\S+",
    r"\b[a-zA-Z0-9.-]+\.(?:top|vip|xyz|cc|site|live)\b",
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
            matched_phrase = found[0] if isinstance(found[0], str) else str(found[0])
            if not any(neg in matched_phrase.lower() for neg in ["न बताएं", "मत बताएं", "साझा न करें", "do not", "never", "झन बताव"]):
                rule_flags["explicit_otp_demand"] = True
                matches.append({"rule": "fraudulent_otp_demand", "phrase": matched_phrase, "risk": True})

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
        risk_score += 0.6
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
