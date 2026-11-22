"""
Scam Stage Tracker for Suraksha
Tracks progression through 4 critical scam stages:
1. Authority Claim
2. Urgency & Panic
3. Request for Sensitive Information
4. Payment Demand
"""

import re

STAGE_DEFINITIONS = {
    "stage_1_authority": {
        "name": "Authority Claim",
        "description": "Scammer poses as Police, CBI, Customs, Electricity Officer, or Bank Manager",
        "patterns": [
            r"\b(?:cbi|police|crime\s+branch|customs|inspector|officer|manager|cspdcl|sbi|hdfc|kbc)\b",
            r"पुलिस|कस्टम|क्राइम\s*ब्रांच|बिजली\s*अधिकारी|बैंक\s*अधिकारी"
        ]
    },
    "stage_2_urgency": {
        "name": "Urgency & Panic",
        "description": "Creating panic with deadlines (2 hours, tonight 9:30, immediate disconnection)",
        "patterns": [
            r"\b(?:immediately|urgent|within\s+2\s+hours|tonight\s+at\s+9:30|disconnected|block|jail|arrest)\b",
            r"तुरंत|आज\s*रात|काट\s*दी\s*जाएगी|जेल|अरेस्ट|ब्लॉक"
        ]
    },
    "stage_3_sensitive_info": {
        "name": "Request for Sensitive Info",
        "description": "Asking for OTP, PIN, CVV, passwords or screen-sharing app installation",
        "patterns": [
            r"\b(?:otp|pin|cvv|password|anydesk|quicksupport|rustdesk|code)\b",
            r"ओटीपी|पिन|सीवीवी|पासवर्ड|एनीडेस्क|कोड"
        ]
    },
    "stage_4_payment": {
        "name": "Payment Demand",
        "description": "Demanding monetary transfer, bond fee, customs tax, or scanning QR",
        "patterns": [
            r"\b(?:transfer|pay|rs\.?\s*\d+|rupees|upi|qr|bond|fine|tax|security\s+deposit)\b",
            r"रुपये|पैसे|भुगतान|जमानत|टैक्स|ट्रांसफर|क्यूआर"
        ]
    }
}

def track_stages(text: str) -> dict:
    text_lower = text.lower()
    stages_detected = []
    max_stage = 0

    for i, (stage_key, stage_info) in enumerate(STAGE_DEFINITIONS.items(), start=1):
        detected = False
        matched_words = []
        for pat in stage_info["patterns"]:
            matches = re.findall(pat, text_lower, flags=re.IGNORECASE)
            if matches:
                detected = True
                matched_words.extend(matches)
        
        if detected:
            stages_detected.append({
                "stage_num": i,
                "stage_key": stage_key,
                "name": stage_info["name"],
                "description": stage_info["description"],
                "matched_words": list(set(matched_words))
            })
            if i > max_stage:
                max_stage = i

    progression_percent = int((len(stages_detected) / 4.0) * 100)

    return {
        "stages": stages_detected,
        "current_stage": max_stage,
        "stage_count": len(stages_detected),
        "progression_percent": progression_percent,
        "is_advanced_scam": max_stage >= 3 and len(stages_detected) >= 2
    }
