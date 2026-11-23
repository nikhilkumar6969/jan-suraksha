"""
Real-Time Scam Detection Engine for Suraksha
Contextual intent recognition and deterministic safety rules across:
1. OTP and PIN Fraud (with immediate Critical hazard on UPI PIN requests)
2. Bank Impersonation & Fake KYC
3. Police & Government Impersonation (Digital Arrest, Fake Subsidies)
4. Financial Fraud (Bail bonds, clearance fees, urgent transfers)
5. Remote Access Fraud (APKs, AnyDesk, QuickSupport, Screen-sharing)
6. Psychological Manipulation (Urgency, fear, secrecy, pressure)

Distinguishes between user narration and attacker solicitation to minimize false positives.
Provides four risk tiers: LOW, MODERATE, HIGH, CRITICAL.
"""

import re
from typing import Dict, Any, List, Optional

# 1. Genuine Safety & User Narration Guards (Contextual False-Positive Reducers)
GENUINE_SAFETY_GUARDS = [
    r"\b(?:do\s+not|never)\s+share\s+(?:your\s+)?(?:otp|pin|password|cvv)\b",
    r"\b(?:bank|police)\s+(?:never|kabhi\s+bhi)\s+(?:calls\s+to\s+)?(?:asks?|mangta)\b",
    r"kisi\s+ko\s+(?:bhi\s+)?(?:na|mat)\s+bataye[mn]?\b",
    r"kisi\s+(?:ko|ke\s+saath)\s+share\s+na\s+kare[mn]?\b",
    r"साझा\s+न\s+करें",
    r"किसी\s+को\s+(?:भी\s+)?न\s+बताएं",
    r"बैंक\s+कभी\s+भी\s+(?:otp|पिन)\s+नहीं\s+मांगता",
    r"ककरो\s+ले\s+साझा\s+झन\s+करव",
    r"ककरो\s+ले\s+झन\s+बताव",
    r"बैंक\s+कभू\s+otp\s+नइ\s+मांगय"
]

USER_NARRATION_PATTERNS = [
    r"\b(?:maine|humne|i\s+have|i\s+already)\s+(?:entered|dala|bhara|diya|paid|pay\s+kar\s+diya)\b",
    r"\b(?:kal|tomorrow|yesterday)\s+(?:bank\s+jaunga|branch\s+jaunga|passbook|milte\s+hain)\b",
    r"\b(?:swiggy|zomato|amazon|flipkart)\s+(?:ka|order|delivery)\s+(?:otp|code)\b",
    r"\b(?:entered\s+the\s+otp\s+myself|i\s+put\s+the\s+otp)\b",
    r"मैंने\s+(?:अपना\s+)?(?:otp|पिन|बिल)\s+(?:डाल\s+दिया|भर\s+दिया|दे\s+दिया)",
    r"कल\s+बैंक\s+जाऊंगा",
    r"बिजली\s+का\s+बिल\s+भर\s+दिया"
]

# 2. OTP and PIN Fraud Patterns
CRITICAL_UPI_PIN_PATTERNS = [
    r"\b(?:enter|put|type|share|give|batao|dalo|daraw)\s+(?:your\s+)?(?:upi\s+)?pin\b",
    r"\bupi\s+pin\s+(?:enter\s+karo|dalo|batao|share\s+kare|daraw|bataw)\b",
    r"\benter\s+pin\s+to\s+(?:receive|accept|get)\s+(?:money|cashback|payment|rupees)\b",
    r"पैसे\s+पाने\s+के\s+लिए\s+upi\s+पिन\s+डालें",
    r"(?:अपना\s+)?upi\s+पिन\s*(?:डालें|बताएं|दर्ज\s+करें|लगाएं)",
    r"पईसा\s+पाए\s+बर\s+upi\s+पिन\s+डारव",
    r"upi\s+पिन\s*(?:डारव|बताव)"
]

EXPLICIT_OTP_PATTERNS = [
    r"\b(?:share|tell|send|forward|give|enter|batao|dalo)\s+(?:me\s+|us\s+)?(?:the\s+|your\s+|apna\s+)?(?:6\s*[-]?\s*digit\s+)?(?:otp|code|pin|verification\s+code)\b",
    r"\botp\s+(?:batao|bataiye|send\s+kar[eo]i?n?|share\s+kar[eo]i?n?|dijiye|forward\s+kar[eo]i?n?|bhejo|bhejei?n?|do|mang\s+raha)\b",
    r"\b(?:apna|your)\s+(?:6\s*[-]?\s*digit\s+)?(?:otp|code|pin)\s+(?:share\s+kar[eo]i?n?|batao|bataiye|bhejo|bhejei?n?|dijiye|batayei?n?)\b",
    r"ओटीपी\s*(?:बताएं|दीजिए|भेजें|शेयर\s+करें|बताओ|डालें)",
    r"मोबाइल\s+म\s+आए\s+(?:otp|कोड)\s+ल\s+(?:बताव|भेजव|डारव)",
    r"ओटीपी\s*(?:बताव|डारव|भेजव)",
    r"otp\s+(?:la\s+bataw|daraw|bhejaw|batao)"
]

# 3. Bank Impersonation & Fake KYC
BANK_IMPERSONATION_PATTERNS = [
    r"\b(?:sbi|hdfc|icici|pnb|bob|bank)\s+(?:customer\s+care|manager|head\s+office|officer|se\s+bol\s+raha)\b",
    r"\b(?:account|yono|sim\s+card|debit\s+card)\s+(?:is\s+)?(?:blocked|suspended|deactivated|frozen|band\s+ho\s+gaya)\b",
    r"\b(?:update|complete)\s+(?:your\s+)?kyc\s+(?:immediately|or\s+blocked)\b",
    r"\bkyc\s+update\s+kar(?:e|o|aw)\s+(?:nahi\s+to|turant)\b",
    r"बैंक\s+(?:अधिकारी|मैनेजर|कस्टमर\s+केयर)\s+बोल\s+रहा\s+हूँ",
    r"खाता\s+(?:बंद|ब्लॉक|सील|फ्रीज)\s+हो\s+गया\s+है",
    r"केवाईसी\s+(?:अपडेट|सत्यापन)\s+तुरंत\s+करें",
    r"तोर\s+खाता\s+बंद\s+हो\s+जाही",
    r"बिजली\s+(?:बिल\s+न[इी]\s+भरे|लाइन\s+कट\s*जाही)",
    r"\belectricity\s+line\s+will\s+be\s+disconnected\s+tonight\b"
]

# 4. Police & Government Impersonation
POLICE_GOVT_PATTERNS = [
    r"\b(?:digital\s+arrest|digitally\s+arrested)\b",
    r"डिजिटल\s+अरेस्ट",
    r"\b(?:mumbai|delhi|cbi|crime\s+branch|customs|cyber\s+cell|ed)\s+(?:police|officer|inspector|headquarters)\b",
    r"\b(?:arrest\s+warrant|fir\s+registered|court\s+order|non-bailable\s+warrant)\b",
    r"\b(?:drugs|narcotics|contraband|illegal\s+passports)\s+in\s+your\s+(?:parcel|aadhaar)\b",
    r"(?:थाना|कोतवाली|क्राइम\s*ब्रांच|सीबीआई).*(?:बोलत\s+हंव|वारंट|जेल)",
    r"थाना\s+(?:कोतवाली|क्राइम\s*ब्रांच|सीबीआई)\s+ले\s+बोलत\s+हंव",
    r"तोर\s+नाम\s+म\s+वारंट",
    r"तोर\s+पार्सल\s+म\s+(?:चरस|गांजा|ड्रग्स)\s+मिले\s+हे",
    r"\b(?:pm\s+awas|mahtari\s+vandan|kisan\s+subsidy)\s+(?:verification|registration\s+fee|approval\s+charge)\b",
    r"महतारी\s+वंदन\s+(?:सत्यापन|पंजीकरण\s+शुल्क)",
    r"प्रधानमंत्री\s+आवास\s+स्वीकृति\s+शुल्क"
]

# 5. Financial Fraud & Extortion
FINANCIAL_EXTORTION_PATTERNS = [
    r"\b(?:bail\s+security\s+bond|clearance\s+fee|penalty\s+charge|penalty\s+fine)\b",
    r"\b(?:transfer|deposit|send|bhejo|jama\s+karo)\s+(?:rs\.?\s*\d+|\d+\s*rupees|\d+\s*hazar|paisa)\b",
    r"\bscan\s+(?:the\s+)?qr\s+code\s+to\s+(?:pay|verify|transfer)\b",
    r"जमानत\s+(?:राशि|बांड)\s+तुरंत\s+जमा\s+करें",
    r"पईसा\s+जमा\s+करव\s+नइ\s+ते\s+जेल\s+भेज\s+देबो",
    r"तुरंत\s+(?:\d+\s*(?:रुपये|हज़ार))\s+(?:भेजें|ट्रांसफर\s+करें)",
    r"क्यूआर\s+कोड\s+स्कैन\s+करके\s+भुगतान\s+करें"
]

# 6. Remote Access Fraud
REMOTE_ACCESS_PATTERNS = [
    r"\b(?:anydesk|quicksupport|teamviewer|rustdesk|zoho\s+assist|screenshare)\b",
    r"एनीडेस्क|क्विक\s*सपोर्ट|टीमव्यूअर",
    r"\b(?:download|install|bheja\s+hai)\s+(?:the\s+)?(?:apk|support\s+app|security\s+app)\b",
    r"\binstall\s+(?:unknown\s+app|customer\s+support\s+apk)\b",
    r"\benable\s+accessibility\s+(?:permission|service)\b",
    r"ऐप\s+(?:डाउनलोड|इन्स्टॉल)\s+करें",
    r"स्क्रीन\s+शेयर\s+करें",
    r"एक्सेसिबिलिटी\s+अनुमति\s+चालू\s+करें"
]

# 7. Psychological Manipulation (Fear, Secrecy, Urgency)
PSYCHOLOGICAL_MANIPULATION_PATTERNS = [
    r"\b(?:do\s+not\s+(?:disconnect|cut)\s+(?:the\s+)?call|phone\s+mat\s+katna|call\s+cut\s+mat\s+karna)\b",
    r"\b(?:stay\s+on\s+(?:video\s+)?call|video\s+call\s+pe\s+bane\s+raho)\b",
    r"\b(?:do\s+not\s+tell\s+anyone|kisi\s+ko\s+mat\s+batana|confidential\s+matter)\b",
    r"\b(?:within\s+10\s+minutes|aaj\s+shaam\s+tak|turant|immediately|aaj\s+raat\s+9:30)\b",
    r"कॉल\s+(?:मत\s+काटना|काटने\s+पर\s+गिरफ्तारी)",
    r"किसी\s+को\s+मत\s+बताना",
    r"वीडियो\s+कॉल\s+पर\s+बने\s+रहें",
    r"कॉल\s+ल\s+झन\s+काटव",
    r"ककरो\s+ले\s+झन\s+बताव",
    r"झन\s+देरी\s+करव"
]


def detect_scam_in_transcript(
    transcript: str,
    user_lang: str = "hi",
    session_history: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluates speech text against fraud categories with intent recognition.
    Returns structured risk assessment matching official civic safety standards.
    """
    text_clean = transcript.strip()
    text_lower = text_clean.lower()

    # Aggregate session history for multi-sentence contextual progression
    all_context = list(session_history) if session_history else []
    all_context.append(text_lower)
    full_context_str = " ".join(all_context).lower()

    # Step 1: Check genuine bank safety warnings & user narration
    is_genuine_alert = False
    for pat in GENUINE_SAFETY_GUARDS:
        if re.search(pat, text_lower, re.IGNORECASE):
            is_genuine_alert = True
            break

    is_user_narration = False
    for pat in USER_NARRATION_PATTERNS:
        if re.search(pat, text_lower, re.IGNORECASE):
            is_user_narration = True
            break

    # Step 2: Category Match Extraction
    matches: Dict[str, List[str]] = {
        "upi_pin_fraud": [],
        "otp_fraud": [],
        "bank_impersonation": [],
        "police_govt_impersonation": [],
        "financial_extortion": [],
        "remote_access": [],
        "psychological_manipulation": []
    }

    def check_pats(patterns: List[str], key: str):
        for pat in patterns:
            found = re.findall(pat, full_context_str, re.IGNORECASE)
            if found:
                for f in found:
                    phrase = f if isinstance(f, str) else f[0]
                    if phrase and phrase not in matches[key]:
                        matches[key].append(phrase)

    check_pats(CRITICAL_UPI_PIN_PATTERNS, "upi_pin_fraud")
    check_pats(EXPLICIT_OTP_PATTERNS, "otp_fraud")
    check_pats(BANK_IMPERSONATION_PATTERNS, "bank_impersonation")
    check_pats(POLICE_GOVT_PATTERNS, "police_govt_impersonation")
    check_pats(FINANCIAL_EXTORTION_PATTERNS, "financial_extortion")
    check_pats(REMOTE_ACCESS_PATTERNS, "remote_access")
    check_pats(PSYCHOLOGICAL_MANIPULATION_PATTERNS, "psychological_manipulation")

    # Step 3: Determine Risk Level & Primary Category
    risk_level = "LOW"
    scam_category = "सामान्य बातचीत (No Threat Detected)"
    reason_hi = "बातचीत में कोई वित्तीय धोखाधड़ी या संदिग्ध संकेत नहीं मिले हैं।"
    reason_en = "No significant suspicious indicators detected in the conversation."
    action_hi = "सतर्क रहें। किसी अनजान व्यक्ति के साथ गुप्त जानकारी कभी साझा न करें।"
    action_en = "Stay vigilant. Never share confidential codes with unverified callers."
    confidence = 0.95

    # Safe override if user was only narrating Swiggy/passbook and no attack patterns
    has_attacks = any(len(matches[k]) > 0 for k in [
        "upi_pin_fraud", "otp_fraud", "police_govt_impersonation",
        "financial_extortion", "remote_access"
    ])

    if (is_genuine_alert or is_user_narration) and not has_attacks:
        return {
            "risk_level": "LOW",
            "is_scam": False,
            "scam_category": "सुरक्षित संदेश / सामान्य बातचीत",
            "reason": "यह एक सामान्य बातचीत या सुरक्षा चेतावनी है। किसी गुप्त कोड की मांग नहीं की गई है।",
            "reason_en": "Normal conversation or genuine security notice. No confidential codes solicited.",
            "recommended_action": "सतर्क रहें। अपना OTP या PIN किसी को न बताएं।",
            "recommended_action_en": "Remain cautious. Never share your OTP or PIN with anyone.",
            "suspicious_phrases": [],
            "matched_categories": [],
            "confidence": 0.98,
            "certainty": "High Confidence"
        }

    # Category & Explanation Dictionaries for Multi-lingual Localization
    CATEGORY_MAP = {
        "upi_pin_fraud": {
            "hi": "UPI PIN चोरी का प्रयास (UPI PIN Fraud)",
            "chg": "UPI पिन चुराए के कोसिस (UPI PIN Fraud)",
            "en": "Urgent UPI PIN Theft Attempt (UPI PIN Fraud)"
        },
        "otp_fraud": {
            "hi": "OTP / सत्यापन कोड चोरी (OTP Theft)",
            "chg": "OTP / गुप्त कोड चुराए के कोसिस (OTP Theft)",
            "en": "OTP / Verification Code Theft"
        },
        "digital_arrest": {
            "hi": "डिजिटल अरेस्ट व जबरन वसूली (Digital Arrest Extortion)",
            "chg": "डिजिटल अरेस्ट अउ पईसा वसूली (Digital Arrest)",
            "en": "Digital Arrest Extortion"
        },
        "remote_access": {
            "hi": "रिमोट एक्सेस ऐप धोखा (Remote Access / APK Fraud)",
            "chg": "मोबाइल हैकिंग ऐप धोखा (Remote Access / APK)",
            "en": "Remote Access / APK Fraud"
        },
        "police_govt_impersonation": {
            "hi": "पुलिस / सरकारी अधिकारी का भेष (Law Enforcement Impersonation)",
            "chg": "पुलिस / अधिकारी बनके ठगी (Impersonation)",
            "en": "Law Enforcement Impersonation"
        },
        "bank_impersonation": {
            "hi": "फर्जी बैंक अधिकारी / KYC बंद की धमकी (Fake Bank KYC Threat)",
            "chg": "फर्जी बैंक / खाता बंद करे के धमकी (Fake Bank KYC)",
            "en": "Fake Bank Officer / KYC Suspension Threat"
        },
        "moderate_urgency": {
            "hi": "संदिग्ध दबाव व बातचीत (Suspicious Claim / Urgency)",
            "chg": "संदेहास्पद दबाव व बातचीत (Suspicious)",
            "en": "Suspicious Claim / Urgency"
        },
        "safe": {
            "hi": "सुरक्षित संदेश / सामान्य बातचीत (No Threat Detected)",
            "chg": "सुरक्षित संदेश / सामान्य बातचीत",
            "en": "Safe / Normal Conversation (No Threat Detected)"
        }
    }

    REASON_MAP = {
        "upi_pin_fraud": {
            "hi": "अत्यंत खतरनाक! कॉलर आपसे UPI PIN दर्ज करने या साझा करने को कह रहा है। पैसे प्राप्त करने के लिए कभी PIN की आवश्यकता नहीं होती।",
            "chg": "भारी खतरा! कॉलर तोर से UPI पिन मांगे के चाल चलत हे। पईसा पाए बर कभू पिन नइ डारे लगत।",
            "en": "CRITICAL HAZARD: Caller is soliciting your UPI PIN. UPI PIN is exclusively for sending money, NEVER for receiving it."
        },
        "otp_fraud": {
            "hi": "कॉलर आपका बैंक सुरक्षा OTP (ओटीपी) चुराने का प्रयास कर रहा है। बैंक या पुलिस कभी भी फोन पर OTP नहीं मांगते।",
            "chg": "कॉलर तोर गुप्त OTP चुराए के चक्कर म हे। बैंक या पुलिस कभू फोन म OTP नइ मांगंय।",
            "en": "Caller is demanding your confidential OTP. Legitimate institutions never solicit OTPs over the phone."
        },
        "digital_arrest": {
            "hi": "कॉलर पुलिस/CBI बनकर डिजिटल अरेस्ट की फर्जी धमकी दे रहा है और जमानत या सुरक्षा राशि की मांग कर रहा है।",
            "chg": "कॉलर पुलिस बनके 'डिजिटल अरेस्ट' के झूठा डर दिखावत हे अउ जमानत के पईसा मांगत हे।",
            "en": "Extortion attempt: Caller is falsely impersonating law enforcement to extort bail/security money under threat of arrest."
        },
        "remote_access": {
            "hi": "कॉलर AnyDesk/QuickSupport ऐप या अज्ञात APK डाउनलोड कराकर आपका फोन हैक करने की कोशिश कर रहा है।",
            "chg": "कॉलर AnyDesk या अनजान APK डाउनलोड करवा के तोर मोबाइल हैक करे के चाल चलत हे।",
            "en": "High risk: Caller is asking to install screen-sharing apps or unknown APK files to compromise your device."
        },
        "police_govt_impersonation": {
            "hi": "कॉलर खुद को पुलिस, कस्टम्स या सरकारी अधिकारी बताकर डराने या धमकी देने का प्रयास कर रहा है।",
            "chg": "कॉलर अपन आप ल पुलिस या सरकारी अधिकारी बताके डरवाए के कोसिस करत हे।",
            "en": "Caller is impersonating police, customs, or government authorities to induce panic."
        },
        "bank_impersonation": {
            "hi": "कॉलर बैंक खाता या बिजली लाइन बंद होने का डर दिखाकर दबाव बना रहा है।",
            "chg": "कॉलर तोर बैंक खाता या बिजली लाइन काटे के डर दिखा के दबाव बनावत हे।",
            "en": "Caller is using false threats of bank suspension or utility disconnection to create urgency."
        },
        "moderate_urgency": {
            "hi": "बातचीत में कृत्रिम जल्दबाजी या संस्थागत दावे के संकेत हैं। कृपया सतर्क रहें।",
            "chg": "बातचीत म संदेहास्पद जल्दीबाजी अउ दबाव दिखत हे। सचेत रहव।",
            "en": "Suspicious institutional claims or urgency detected. Proceed with caution."
        },
        "safe": {
            "hi": "यह एक सामान्य बातचीत या सुरक्षा चेतावनी है। किसी गुप्त कोड की मांग नहीं की गई है।",
            "chg": "ये सामान्य बातचीत आय। कोनो गुप्त कोड या पईसा नइ मांगे गे हे।",
            "en": "Normal conversation or genuine security notice. No confidential codes solicited."
        }
    }

    ACTION_MAP = {
        "upi_pin_fraud": {
            "hi": "कॉल तुरंत काटें! कभी भी अपना UPI PIN दर्ज न करें। बैंक खाते को सुरक्षित करने के लिए 1930 पर कॉल करें।",
            "chg": "कॉल ल तुरते काटव! कभू अपन UPI पिन झन डारव। 1930 म फोन लगाके शिकायत करव।",
            "en": "Disconnect immediately! Never enter your UPI PIN. Dial 1930 National Helpline to protect your funds."
        },
        "otp_fraud": {
            "hi": "कॉल तुरंत डिस्कनेक्ट करें। किसी भी व्यक्ति को OTP न बताएं। बैंक से तुरंत संपर्क करें।",
            "chg": "कॉल तुरते काटव। ककरो ले अपन OTP झन बतावव। अपन बैंक म जाके मिलव।",
            "en": "Hang up immediately. Never disclose your OTP. Contact your bank branch directly."
        },
        "digital_arrest": {
            "hi": "कॉल तुरंत काटें। भारत में 'डिजिटल अरेस्ट' का कोई कानून नहीं है। 1930 पर शिकायत दर्ज करें।",
            "chg": "कॉल तुरते काटव। कानून म 'डिजिटल अरेस्ट' नइ होवय। तुरते 1930 म शिकायत करव।",
            "en": "Hang up immediately. 'Digital arrest' is completely fabricated. Report directly to 1930."
        },
        "remote_access": {
            "hi": "कोई भी ऐप इंस्टॉल न करें और स्क्रीन शेयर न करें। कॉल तुरंत डिस्कनेक्ट करें।",
            "chg": "कोनो अनजान ऐप डाउनलोड झन करव अउ स्क्रीन शेयर झन करव। फोन ल तुरते काटव।",
            "en": "Do NOT install any APK or screen-sharing app. Disconnect the call right away."
        },
        "police_govt_impersonation": {
            "hi": "घबराएं नहीं। फोन काटें और स्थानीय थाने या 1930 हेल्पलाइन पर कॉल कर पुष्टि करें।",
            "chg": "झन डरवाव। फोन काटव अउ अपन नजदीकी थाना या 1930 म पूछ लेवव।",
            "en": "Do not panic. Hang up and verify through official police channels or dial 1930."
        },
        "bank_impersonation": {
            "hi": "किसी अनजान नंबर पर भरोसा न करें। सीधे अपनी बैंक शाखा या बिजली विभाग से संपर्क करें।",
            "chg": "अनजान नंबर म भरोसा झन करव। सीधा अपन बैंक या बिजली दफ्तर म जाके पता करव।",
            "en": "Do not trust unsolicited callers. Visit your official bank branch or utility office directly."
        },
        "moderate_urgency": {
            "hi": "बातचीत को ध्यान से सुनें। कोई भी निजी कोड, पासवर्ड या पैसे ट्रांसफर न करें।",
            "chg": "गोठ-बात ल ध्यान से सुनव। कोनो गुप्त कोड या पईसा ट्रांसफर झन करव।",
            "en": "Listen carefully. Do not transfer funds or share any personal verification codes."
        },
        "safe": {
            "hi": "सतर्क रहें। अपना OTP या PIN किसी को न बताएं।",
            "chg": "सचेत रहव। अपन OTP या पिन ककरो ले झन बतावव।",
            "en": "Remain cautious. Never share your OTP or PIN with anyone."
        }
    }

    # CRITICAL Hazard: UPI PIN request (Immediate money siphon hazard)
    eval_key = "safe"
    if len(matches["upi_pin_fraud"]) > 0:
        risk_level = "CRITICAL"
        eval_key = "upi_pin_fraud"
        confidence = 0.99
    elif len(matches["otp_fraud"]) > 0:
        risk_level = "CRITICAL"
        eval_key = "otp_fraud"
        confidence = 0.98
    elif len(matches["police_govt_impersonation"]) > 0 and len(matches["financial_extortion"]) > 0:
        risk_level = "CRITICAL"
        eval_key = "digital_arrest"
        confidence = 0.98
    elif len(matches["remote_access"]) > 0:
        risk_level = "HIGH"
        eval_key = "remote_access"
        confidence = 0.95
    elif len(matches["police_govt_impersonation"]) > 0:
        risk_level = "HIGH"
        eval_key = "police_govt_impersonation"
        confidence = 0.92
    elif len(matches["bank_impersonation"]) > 0 and (
        len(matches["psychological_manipulation"]) > 0 or 
        any(k in full_context_str for k in ["block", "suspend", "band", "freeze", "kyc", "yono", "बंद", "ब्लॉक", "सील", "कट जाही", "पईसा"])
    ):
        risk_level = "HIGH"
        eval_key = "bank_impersonation"
        confidence = 0.90
    elif len(matches["bank_impersonation"]) > 0 or len(matches["psychological_manipulation"]) > 0:
        risk_level = "MODERATE"
        eval_key = "moderate_urgency"
        confidence = 0.75
    else:
        risk_level = "LOW"
        eval_key = "safe"
        confidence = 0.95

    # Safe override if user was only narrating Swiggy/passbook and no attack patterns
    if (is_genuine_alert or is_user_narration) and not has_attacks:
        risk_level = "LOW"
        eval_key = "safe"
        confidence = 0.98

    # Multi-lingual lookups
    target_lang = user_lang if user_lang in ("hi", "chg", "en") else "hi"
    scam_category = CATEGORY_MAP[eval_key].get(target_lang, CATEGORY_MAP[eval_key]["hi"])
    reason = REASON_MAP[eval_key].get(target_lang, REASON_MAP[eval_key]["hi"])
    recommended_action = ACTION_MAP[eval_key].get(target_lang, ACTION_MAP[eval_key]["hi"])

    # Gather all matched suspicious phrases
    suspicious_phrases = []
    active_categories = []
    for cat_name, phrase_list in matches.items():
        if phrase_list:
            active_categories.append(cat_name)
            suspicious_phrases.extend(phrase_list)

    # Audio warning text generation (Hindi & English)
    audio_warning_hi = ""
    audio_warning_en = ""
    if risk_level == "CRITICAL":
        if "upi_pin_fraud" in active_categories:
            audio_warning_hi = "सावधान! किसी को भी अपना UPI पिन न बताएं और न ही दर्ज करें। पैसे पाने के लिए पिन की जरूरत नहीं होती।"
            audio_warning_en = "Warning! Never enter or disclose your UPI PIN. UPI PIN is never needed to receive money."
        else:
            audio_warning_hi = "सावधान! किसी को भी अपना OTP या बैंक कोड न बताएं। कॉल तुरंत काटें।"
            audio_warning_en = "Alert! Never share your OTP or bank codes. Hang up the call immediately."
    elif risk_level == "HIGH":
        if "remote_access" in active_categories:
            audio_warning_hi = "सतर्क रहें! कोई भी ऐप या APK डाउनलोड न करें। यह ठगी का प्रयास हो सकता है।"
            audio_warning_en = "Caution! Do not install any app or APK. This may be a fraudulent attempt."
        else:
            audio_warning_hi = "सतर्क रहें! पुलिस या बैंक कभी फोन पर पैसे या गिरफ्तारी की धमकी नहीं देते।"
            audio_warning_en = "Be cautious! Official authorities never threaten arrest or demand money over the phone."
    elif risk_level == "MODERATE":
        audio_warning_hi = "ध्यान दें! बातचीत संदिग्ध लग रही है। कोई भी गोपनीय जानकारी न दें।"
        audio_warning_en = "Notice! Conversation seems suspicious. Do not share confidential information."

    return {
        "risk_level": risk_level,
        "is_scam": risk_level in ("HIGH", "CRITICAL"),
        "scam_category": scam_category,
        "scam_category_hi": CATEGORY_MAP[eval_key]["hi"],
        "scam_category_chg": CATEGORY_MAP[eval_key]["chg"],
        "scam_category_en": CATEGORY_MAP[eval_key]["en"],
        "reason": reason,
        "reason_hi": REASON_MAP[eval_key]["hi"],
        "reason_chg": REASON_MAP[eval_key]["chg"],
        "reason_en": REASON_MAP[eval_key]["en"],
        "recommended_action": recommended_action,
        "recommended_action_hi": ACTION_MAP[eval_key]["hi"],
        "recommended_action_chg": ACTION_MAP[eval_key]["chg"],
        "recommended_action_en": ACTION_MAP[eval_key]["en"],
        "audio_warning_hi": audio_warning_hi,
        "audio_warning_en": audio_warning_en,
        "suspicious_phrases": list(set(suspicious_phrases)),
        "matched_categories": active_categories,
        "confidence": confidence,
        "certainty": f"{int(confidence * 100)}% Certainty"
    }
