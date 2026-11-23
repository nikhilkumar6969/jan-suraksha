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
    r"ककरो\s+ले\s+(?:अपन\s+)?(?:गुप्त\s+)?(?:otp|ओटीपी|पिन)\s+झन\s+(?:बताव|बतावव|शेयर\s+करव)",
    r"ककरो\s+ले\s+झन\s+बताव",
    r"बैंक\s+कभू\s+(?:फोन\s+म\s+)?(?:otp|पिन)\s+नइ\s+मांगय",
    r"पुलिस\s+कभू\s+(?:फोन\s+म\s+)?जमानत\s+नइ\s+मांगय",
    r"कोनो\s+अनजान\s+ऐप\s+डाउनलोड\s+झन\s+करव",
    r"अपन\s+पिन\s+ल\s+छुपा\s+के\s+राखव"
]

USER_NARRATION_PATTERNS = [
    r"\b(?:maine|humne|i\s+have|i\s+already)\s+(?:entered|dala|bhara|diya|paid|pay\s+kar\s+diya)\b",
    r"\b(?:kal|tomorrow|yesterday)\s+(?:bank\s+jaunga|branch\s+jaunga|passbook|milte\s+hain)\b",
    r"\b(?:swiggy|zomato|amazon|flipkart)\s+(?:ka|order|delivery)\s+(?:otp|code)\b",
    r"\b(?:entered\s+the\s+otp\s+myself|i\s+put\s+the\s+otp)\b",
    r"मैंने\s+(?:अपना\s+)?(?:otp|पिन|बिल)\s+(?:डाल\s+दिया|भर\s+दिया|दे\s+दिया)",
    r"कल\s+बैंक\s+जाऊंगा",
    r"बिजली\s+का\s+बिल\s+भर\s+दिया",
    r"मंय\s+खुद\s+बैंक\s+जाके",
    r"मंय\s+(?:अपन\s+)?(?:बिल|प[ईइ]सा|रुपिया)\s+पटा\s+दे\s+हंव",
    r"पासबुक\s+(?:चढ़ाए|एंट्री|अपडेट)\s+बर\s+जाबो",
    r"डिलीवरी\s+आइस\s+त\s+ओटीपी\s+दे\s+रहेव",
    r"मंय\s+खुद\s+डारे\s+हंव"
]

# 2. OTP and PIN Fraud Patterns
CRITICAL_UPI_PIN_PATTERNS = [
    r"\b(?:enter|put|type|share|give|batao|dalo|daraw|bataw|darahu|batahu)\s+(?:your\s+|tor\s+|apna\s+)?(?:upi\s+)?pin\b",
    r"\bupi\s+pin\s+(?:enter\s+karo|dalo|batao|share\s+kare|daraw|bataw|darahu|batahu)\b",
    r"\benter\s+pin\s+to\s+(?:receive|accept|get)\s+(?:money|cashback|payment|rupees)\b",
    r"\b(?:paisa|rupaye)\s+(?:paye\s+bar|milahi)\s+(?:upi\s+)?pin\s+(?:daraw|bataw|dalo)\b",
    r"\b(?:should\s+i|do\s+i\s+need\s+to|asking\s+me\s+to)\s+(?:enter|put|type|share)\s+(?:my\s+|the\s+)?(?:upi\s+)?pin\b",
    r"\b(?:scan\s+(?:the\s+|a\s+)?qr\s+code\s+to\s+(?:receive|get|claim)\s+(?:money|prize|cashback|amount|reward))\b",
    r"\b(?:receive|get|claim)\s+(?:money|cashback|prize)\s+.*?\b(?:qr\s+code|upi\s+pin|pin)\b",
    r"पैसे\s+पाने\s+के\s+लिए\s+upi\s+पिन\s+डालें",
    r"(?:अपना\s+)?upi\s+पिन\s*(?:डालें|बताएं|दर्ज\s+करें|लगाएं)",
    r"प[ईइ]सा\s+पाए\s+बर\s+upi\s+पिन\s*(?:डारव|बताव|डारहु|बताहू|डालव)",
    r"खाता\s+म\s+प[ईइ]सा\s+आही\s+upi\s+पिन\s+डारव",
    r"प[ईइ]सा\s+मिले\s+बर\s+पिन\s+डारव",
    r"upi\s+पिन\s*(?:डारव|बताव|डारहू|बताहू|डार|डालव)"
]

EXPLICIT_OTP_PATTERNS = [
    r"\b(?:share|tell|send|forward|give|enter|batao|dalo|bataw|daraw)\s+(?:me\s+|us\s+)?(?:the\s+|your\s+|apna\s+|tor\s+)?(?:6\s*[-]?\s*digit\s+)?(?:otp|code|pin|verification\s+code)\b",
    r"\botp\s+(?:la\s+)?(?:batao|bataiye|send\s+kar[eo]i?n?|share\s+kar[eo]i?n?|dijiye|forward\s+kar[eo]i?n?|bhejo|bhejei?n?|do|mang\s+raha|bataw|daraw|bhejaw|darahu|batahu)\b",
    r"\b(?:apna|your|tor)\s+(?:6\s*[-]?\s*digit\s+)?(?:otp|code|pin)\s+(?:share\s+kar[eo]i?n?|batao|bataiye|bhejo|bhejei?n?|dijiye|batayei?n?|bataw|daraw|batahu)\b",
    r"\b(?:asking\s+(?:for|me\s+for)|should\s+i\s+tell|can\s+i\s+share)\s+(?:my\s+|the\s+)?(?:otp|code|pin|verification\s+code)\b",
    r"ओटीपी\s*(?:बताएं|दीजिए|भेजें|शेयर\s+करें|बताओ|डालें|बताव|डारव|भेजव|बताहू|डारहू|बतावव)",
    r"मोबाइल\s+म\s+आए\s+(?:otp|कोड|ओटीपी|नंबर)\s+ल\s+(?:बताव|भेजव|डारव|बताहू|डारहू|बतावव)",
    r"6\s*अंक\s+के\s+(?:कोड|ओटीपी|नंबर)\s*(?:आइस\s+हे\s*,?\s*)?(?:ओला|एला|ला|ल)?\s*(?:जल्दी\s+)?(?:बताव|डारव|बतावव|बताहू|डारहू)",
    r"(?:ओटीपी|otp|कोड)\s*(?:आइस\s+हे\s*,?\s*)?(?:ओला|एला|ला|ल)?\s*(?:जल्दी\s+)?(?:बताव|डारव|भेजव|बताहू|डारहू|बतावव)",
    r"(?:otp|ओटीपी|कोड)\s*(?:ला|ल|ओला)?\s*(?:बताव|बतावव|डारव|डारहू|बताहू)",
    r"सत्यापन\s+बर\s+(?:otp|ओटीपी|कोड)",
    r"ओटीपी\s*(?:बताव|डारव|भेजव|बताहू|बतावव)",
    r"otp\s+(?:la\s+bataw|daraw|bhejaw|batao)"
]

# 3. Bank Impersonation & Fake KYC
BANK_IMPERSONATION_PATTERNS = [
    r"\b(?:sbi|hdfc|icici|pnb|bob|bank)\s+(?:customer\s+care|manager|head\s+office|officer|se\s+bol\s+raha|le\s+bolat\s+hanw|department|verification)\b",
    r"\b(?:account|yono|sim\s+card|debit\s+card|credit\s+card)\s+(?:is\s+)?(?:blocked|suspended|deactivated|frozen|band\s+ho\s+gaya|band\s+ho\s+jahi|upgrade|expired)\b",
    r"\b(?:account|khata|bank|debit\s+card|credit\s+card|atm|sim)\b.*?\b(?:block|band|suspend|freeze|deactivat\w*)\b",
    r"\b(?:update|complete)\s+(?:your\s+)?kyc\s+(?:immediately|or\s+blocked)\b",
    r"\bkyc\s+update\s+kar(?:e|o|aw|waw)\s+(?:nahi\s+to|turant|nai\s+te)\b",
    r"बैंक\s+(?:अधिकारी|मैनेजर|कस्टमर\s+केयर)\s+बोल\s+रहा\s+हूँ",
    r"बैंक\s+ले\s+बोलत\s+हंव",
    r"खाता\s+(?:बंद|ब्लॉक|सील|फ्रीज)\s+हो\s+गया\s+है|खाता\s+ब्लॉक\s+होने\s+का|अकाउंट\s+ब्लॉक",
    r"केवाईसी\s+(?:अपडेट|सत्यापन)\s+तुरंत\s+करें",
    r"तोर\s+खाता\s+बंद\s+हो\s+(?:जाही|गे\s+हे|गिस)",
    r"तोर\s+(?:पासबुक|एटीएम|yono)\s+ब्लॉक\s+हो\s+जाही",
    r"शाखा\s+जाए\s+के\s+जरूरत\s+न[इी]\s+हे,\s+घर\s+बैठे\s+kyc\s+करवाव"
]

# 4. Utility & Electricity Disconnection Threats
UTILITY_ELECTRICITY_PATTERNS = [
    r"\b(?:electricity|power|bijli)\b.*?\b(?:disconnect\w*|cut\s*off|shut\s*off|kat\s*jae\w*|kat\s*jahi|seal\w*|unpaid|arrears)\b",
    r"\b(?:will\s+(?:my\s+)?electricity\s+.*?(?:disconnect\w*|cut)|power\s+cut\s+tonight)\b",
    r"\b(?:bijli|electricity|line|meter|power|light)\b.*?\b(?:kaat|cut|band|disconnect|unpaid|arrears)\b",
    r"\bline\s+kaat\s+rahe\s+hain\b",
    r"\b(?:meter\s+reading|cspdcl|power\s+department|electricity\s+officer)\b",
    r"(?:बिजली|लाइन|मीटर|कनेक्शन)\s+.*?(?:काट\s+दी\s+जाएगी|काट\s+दिया\s+जाएगा|काट\s+दिया\s+जायेगा|कट\s*जाही|कट\s+जाएगी|कट\s+जाएगा|सील\s+हो\s+जाही|डिस्कनेक्ट)",
    r"बिजली\s+(?:कनेक्शन\s+)?(?:काट\s+दी\s+जाएगी|काट\s+दिया\s+जाएगा|काट\s+दिया\s+जायेगा|बिल\s+न[इी]\s+भरे|लाइन\s+कट\s*जाही|मीटर\s+सील|कटने\s+ले\s+बचाए)",
    r"बिजली\s+बिल\s+अपडेट\s+नहीं\s+हुआ\s+है",
    r"लाइन\s+काट\s+रहे\s+हैं",
    r"संझा\s+9:30\s+बजे\s+(?:तोर\s+घर\s+के\s+)?बिजली\s+(?:लाइन\s+)?कट\s*जाही",
    r"लाइन\s+कटने\s+ले\s+बचाए\s+बर.*(?:फोन\s+लगाके\s+)?प[ईइ]सा\s+पटाव",
    r"(?:cspdcl|बिजली)\s+(?:ऑफिस|दफ्तर|अधिकारी)\s+ले\s+बोलत\s+हंव",
    r"मीटर\s+सील\s+हो\s+जाही",
    r"\belectricity\s+line\s+will\s+be\s+disconnected\s+tonight\b",
    r"\bbijli\s+bill\s+nai\s+bhare\s+has\b"
]

# 5. Police & Government Impersonation (Digital Arrest)
POLICE_GOVT_PATTERNS = [
    r"\b(?:digital\s+arrest|digitally\s+arrested)\b",
    r"\b(?:is\s+)?digital\s+arrest\s+(?:real|fake|true|possible|legal)\b",
    r"\b(?:why\s+is\s+|is\s+it\s+real\s+that\s+|can\s+)?(?:cbi|police|inspector|crime\s+branch|ed|customs)\b.*?\b(?:calling|call|whatsapp|video\s+call)\b",
    r"डिजिटल\s+अरेस्ट",
    r"डिजिटल\s+अरेस्ट\s+(?:असली|नकली|सच|होता\s+है)",
    r"डिजिटल\s+अरेस्ट\s+म\s+हस",
    r"\b(?:mumbai|delhi|cbi|crime\s+branch|customs|cyber\s+cell|ed)\s+(?:police|officer|inspector|headquarters)\b",
    r"\b(?:arrest\s+warrant|fir\s+registered|court\s+order|non-bailable\s+warrant)\b",
    r"\b(?:arrest\s+me|threaten\s+to\s+arrest|arrested|going\s+to\s+arrest|send\s+to\s+jail|put\s+in\s+jail|warrant\s+issued)\b",
    r"\b(?:police|cbi|inspector|daroga|thana)\s+.*?(?:fine|bail|arrest|jail|threat|demand|case|fir)\b",
    r"\b(?:why\s+is\s+police|is\s+police\s+calling|am\s+i\s+under\s+arrest)\b",
    r"\b(?:drugs|narcotics|contraband|illegal\s+passports)\s+in\s+your\s+(?:parcel|aadhaar)\b",
    r"(?:थाना|कोतवाली|क्राइम\s*ब्रांच|सीबीआई|सिविल\s+लाइन).*(?:बोलत\s+हंव|वारंट|जेल|गिरफ्तार)",
    r"थाना\s+(?:कोतवाली|क्राइम\s*ब्रांच|सीबीआई|सिविल\s+लाइन)\s+ले\s+बोलत\s+हंव",
    r"तोर\s+नाम\s+म\s+(?:गैर\s*जमानती\s+)?वारंट\s+निकल\s+गे\s+हे",
    r"तोर\s+नाम\s+म\s+(?:भारी\s+)?बड़ा\s+केस\s+बने\s+हे",
    r"पुलिस\s+आके\s+उठा\s+ले\s+जाही",
    r"मामला\s+रफा\s*दफा\s+करे\s+बर",
    r"तोर\s+पार्सल\s+म\s+(?:चरस|गांजा|ड्रग्स|नशीली\s+दवा)\s+मिले\s+हे"
]

# 6. Courier & Customs Extortion
COURIER_CUSTOMS_PATTERNS = [
    r"\b(?:fedex|dhl|bluedart|customs|parcel|package|consignment)\s+.*?(?:illegal|drugs|narcotics|contraband|clearance|fee|detained|held)\b",
    r"\b(?:customs\s+clearance|customs\s+duty|illegal\s+parcel|package\s+detained)\b",
    r"पार्सल\s+म\s+(?:चरस|गांजा|ड्रग्स|नशीली\s+दवा)|कस्टम्स\s+क्लियरेंस\s+फीस",
    r"कस्टम्स\s+अधिकारी|अवैध\s+पार्सल"
]

# 7. Lottery & Fake Subsidies (Mahtari Vandan, PM Awas)
LOTTERY_SUBSIDY_PATTERNS = [
    r"\b(?:lottery|kbc|cashback|prize|reward|winner|lucky\s+draw)\s+.*?(?:fee|charge|deposit|paisa|claim|amount|jeete)\b",
    r"\b(?:win\s+(?:a\s+)?lottery|lottery\s+without|prize\s+money|receive\s+prize|claim\s+(?:cashback|reward|lottery))\b",
    r"\b(?:pm\s+awas|mahtari\s+vandan|kisan\s+subsidy)\s+(?:verification|registration\s+fee|approval\s+charge|shulk)\b",
    r"महतारी\s+वंदन\s+योजना\s+के\s+(?:\d+\s+रुप[ईय]ा\s+)?अटके\s+हे",
    r"महतारी\s+वंदन\s+(?:सत्यापन|पंजीकरण\s+शुल्क)",
    r"योजना\s+के\s+राशि\s+पाए\s+बर.*(?:प[ईइ]सा|शुल्क|फीस)\s+(?:पटाव|जमा\s+करव)",
    r"प्रधानमंत्री\s+आवास\s+(?:योजना\s+)?(?:के\s+प[ईइ]सा|स्वीकृति\s+शुल्क)",
    r"किसान\s+न्याय\s+योजना\s+बोनस\s+सत्यापन\s+शुल्क",
    r"(?:पीएम\s+किसान|pm\s+kisan|किसान\s+सम्मान\s+निधि).*(?:किस्त\s+रुके\s+हे|केवाईसी|अटके\s+हे|प[ईइ]सा\s+आही)",
    r"(?:सौर\s+सुजला|सोलर\s+पंप|सौर\s+पंप).*(?:सब्सिडी|पंजीकरण\s+शुल्क|स्वीकृति|प[ईइ]सा\s+पटाव)",
    r"(?:धान\s+बोनस|धान\s+खरीदी).*(?:प[ईइ]सा\s+अटका\s+हे|अटके\s+हे|भुगतान\s+बर|खाता\s+वेरिफाई)",
    r"(?:केबीसी|kbc|लाटरी|लॉटरी|इनाम|crorepati|करोड़पति).*(?:25\s*लाख|लाख|लॉटरी\s+लगी|जीते\s+ह[ैंस]|लगे\s+हे|पाए\s+बर.*प[ईइ]सा|फाइल\s+चार्ज|ट्रांसफर\s+कराने)",
    r"\b(?:25\s*lakh|lottery\s+winner|kbc\s+lottery|file\s+charge|processing\s+charge)\b",
    r"लॉटरी\s+जीत|इनाम\s+मिला|कैशबैक\s+पाएं|लॉटरी\s+लगी\s+है"
]

# 8. Financial Fraud & Extortion Demands
FINANCIAL_EXTORTION_PATTERNS = [
    r"\b(?:part[- ]time\s+job|work\s+from\s+home|youtube\s+(?:like|subscribe)|telegram\s+group)\b.*?\b(?:earn|daily|per\s+day|fees?|registration|deposit|jama)\b",
    r"(?:घर\s+बैठे|पार्ट\s*टाइम\s*जॉब|यूट्यूब\s+वीडियो\s+लाइक|टेलीग्राम\s+ग्रुप).*(?:कमाएं|कमाने|रजिस्ट्रेशन\s+फीस|पंजीकरण\s+शुल्क|जमा\s+करें|कमाव)",
    r"\b(?:bail\s+security\s+bond|clearance\s+fee|penalty\s+charge|penalty\s+fine|file\s+charge)\b",
    r"\b(?:transfer|deposit|send|bhejo|jama\s+karo|pataw|patai)\s+(?:rs\.?\s*\d+|\d+\s*rupees|\d+\s*hazar|paisa|paisa\s+pataw)\b",
    r"\b(?:how\s+much\s+fine|how\s+much\s+penalty|fine\s+do\s+i\s+need\s+to\s+deposit|pay\s+fine|deposit\s+fine)\b",
    r"\bscan\s+(?:the\s+)?qr\s+code\s+to\s+(?:pay|verify|transfer)\b",
    r"जमानत\s+(?:राशि|बांड)\s+तुरंत\s+जमा\s+करें",
    r"जमानत\s+(?:राशि|के\s+प[ईइ]सा|बांड)\s+तुरत[े]?\s+पटाव",
    r"प[ईइ]सा\s+(?:तुरते\s+)?(?:पटाव|जमा\s+करव)\s+न[इी]\s+ते\s+जेल\s+भेज\s+देबो",
    r"क्लियरेंस\s+फीस\s+पटाव",
    r"तुरंत\s+(?:\d+\s*(?:रुपये|हज़ार|हजार|प[ईइ]सा))\s+(?:भेजें|ट्रांसफर\s+करें|पटाव)",
    r"\d+\s*(?:हज़ार|हजार|रुपया|रुपिया|प[ईइ]सा)\s+(?:तुरते\s+)?(?:पटाव|जमा\s+करव|ट्रांसफर\s+करव)",
    r"प[ईइ]सा\s+पटाव\s+न[इी]\s+ते",
    r"क्यूआर\s+कोड\s+स्कैन\s+करके\s+भुगतान\s+करें",
    r"जुर्माना\s+भर|कतका\s+पईसा\s+पटाना\s+पड़ही"
]

# 9. Remote Access Fraud & Computer Takeover
REMOTE_ACCESS_PATTERNS = [
    r"\b(?:anydesk|quicksupport|teamviewer|rustdesk|zoho\s+assist|screenshare)\b",
    r"एनीडेस्क|क्विक\s*सपोर्ट|टीमव्यूअर",
    r"\b(?:you\s+need|need\s+a|have\s+a|open|turn\s+on|switch\s+on|start|go\s+to|use)\s+(?:a\s+|your\s+)?(?:computer|pc|laptop|desktop)\b",
    r"\b(?:computer|laptop|pc)\s+(?:on\s+karo|chalu\s+karo|start\s+karo|open\s+karo|me\s+connect)\b",
    r"\b(?:need\s+a\s+computer|access\s+your\s+computer|connect\s+your\s+computer)\b",
    r"\b(?:should\s+i\s+download|how\s+to\s+download|told\s+me\s+to\s+download|install)\s+(?:anydesk|quicksupport|teamviewer|rustdesk|screen\s+share)\b",
    r"\b(?:screen\s+share|view\s+my\s+screen|remote\s+access)\b",
    r"कंप्यूटर\s*(?:चालू\s+करो|खोलो|ऑन\s+करो|पे\s+बैठो|में\s+देखो|चाहिए)",
    r"लैपटॉप\s*(?:चालू\s+करो|खोलो|ऑन\s+करो)",
    r"\b(?:download|install|bheja\s+hai|bheje\s+hanw)\s+(?:the\s+)?(?:apk|support\s+app|security\s+app)\b",
    r"\binstall\s+(?:unknown\s+app|customer\s+support\s+apk)\b",
    r"\benable\s+accessibility\s+(?:permission|service)\b",
    r"व्हाट्सएप\s+म\s+(?:फाइल|ऐप|लिंक)\s+भेजे\s+हंव\s+ओला\s+(?:डाउनलोड|इन्स्टॉल)\s+करव",
    r"(?:anydesk|quicksupport|teamviewer)\s+(?:डाउनलोड\s+करके|म\s+स्क्रीन\s+शेयर\s+करव)",
    r"ऐप\s+ल\s+(?:डाउनलोड|इन्स्टॉल)\s+करव",
    r"ऐप\s+(?:डाउनलोड|इन्स्टॉल)\s+करें",
    r"स्क्रीन\s+शेयर\s+(?:करें|करव|चालू\s+करव)",
    r"एक्सेसिबिलिटी\s+अनुमति\s+चालू\s+करें"
]

# 10. Identity & Official Inquiry (User Question Verification)
IDENTITY_INQUIRY_PATTERNS = [
    r"\b(?:who\s+(?:are\s+you|is\s+this|is\s+calling)|where\s+is\s+your\s+(?:office|branch)|what\s+is\s+your\s+(?:name|id|employee\s+id|designation)|can\s+you\s+send\s+official|prove\s+your\s+identity)\b",
    r"आप\s+कौन\s+हो|कहाँ\s+से\s+बोल\s+रहे|कौन\s+सी\s+शाखा|पहचान\s+पत्र|आईडी\s+कार्ड|तुम्हारा\s+नाम\s+क्या\s+है",
    r"तूं\s+कोन\s+बोलत\s+हस|कहाँ\s+ले\s+बोलत\s+हस|ऑफिस\s+कहाँ\s+हे|तोर\s+नाम\s+का\s+हे"
]

# 11. Safe Banking & Procedural Inquiry
BANKING_INQUIRY_PATTERNS = [
    r"\b(?:check\s+(?:my\s+)?(?:bank\s+|account\s+)?balance|how\s+(?:do\s+i|can\s+i|to)\s+check\s+.*balance|account\s+balance|passbook|cheque\s*book|working\s+hours|atm\s+card\s+apply)\b",
    r"\b(?:how\s+(?:do\s+i|can\s+i|to)\s+update\s+(?:my\s+)?kyc\s+safely|safe\s+kyc|visit\s+(?:my\s+)?(?:bank\s+)?branch)\b",
    r"बैलेंस\s+(?:कैसे\s+देखें|जांचें)|पासबुक\s+(?:एंट्री|अपडेट)|चेकबुक|शाखा\s+का\s+समय|खाते\s+की\s+जानकारी",
    r"बैलेंस\s+कइसे\s+देखबो|पासबुक\s+चढ़ाए\s+बर|खाता\s+म\s+कतका\s+पईसा\s+हे",
    r"शाखा\s+जाके\s+(?:kyc|केवाईसी)|सुरक्षित\s+तरीके\s+से\s+(?:kyc|केवाईसी)|शाखा\s+जाकर\s+सुरक्षित\s+(?:केवाईसी|kyc)"
]

# 12. 1930 Cyber Fraud Reporting Inquiry
CYBER_REPORTING_INQUIRY_PATTERNS = [
    r"\b(?:how\s+(?:do\s+i|to)\s+report|report\s+(?:cyber\s+fraud|scam|to\s+1930)|what\s+is\s+1930|call\s+1930|file\s+(?:a\s+)?complaint|cybercrime\.gov\.in|where\s+to\s+complain)\b",
    r"1930\s*(?:म|पर|हेल्पलाइन|शिकायत|कॉल)|शिकायत\s+कैसे\s+करें|साइबर\s+क्राइम\s+रिपोर्ट|ठगी\s+की\s+शिकायत"
]

# 7. Psychological Manipulation (Fear, Secrecy, Urgency)
PSYCHOLOGICAL_MANIPULATION_PATTERNS = [
    r"\b(?:do\s+not\s+(?:disconnect|cut)\s+(?:the\s+)?call|phone\s+mat\s+katna|call\s+cut\s+mat\s+karna)\b",
    r"\b(?:stay\s+on\s+(?:video\s+)?call|video\s+call\s+pe\s+bane\s+raho|video\s+call\s+m\s+bane\s+rahav)\b",
    r"\b(?:do\s+not\s+tell\s+anyone|kisi\s+ko\s+mat\s+batana|confidential\s+matter|kisi\s+ko\s+jhan\s+batav)\b",
    r"\b(?:within\s+10\s+minutes|aaj\s+shaam\s+tak|turant|immediately|aaj\s+raat\s+9:30|sanjha\s+tak)\b",
    r"कॉल\s+(?:मत\s+काटना|काटने\s+पर\s+गिरफ्तारी)",
    r"किसी\s+को\s+मत\s+बताना",
    r"वीडियो\s+कॉल\s+पर\s+बने\s+रहें",
    r"कॉल\s+ल\s+झन\s+काटव",
    r"ककरो\s+ले\s+झन\s+बताव(?:व)?",
    r"घर\s+के\s+मनखे\s+ल\s+झन\s+बताव",
    r"झन\s+देरी\s+करव",
    r"संझा\s+तक\s+काम\s+नइ\s+होही\s+त\s+कार्रवाई\s+होही",
    r"वीडियो\s+कॉल\s+म\s+बने\s+रहव"
]


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
    "utility_electricity": {
        "hi": "बिजली बिल / लाइन काटने की धमकी (Electricity Utility Threat)",
        "chg": "बिजली लाइन काटे के धमकी (Electricity Threat)",
        "en": "Electricity Disconnection Threat (Utility Scam)"
    },
    "courier_customs": {
        "hi": "फर्जी कूरियर / कस्टम्स पार्सल धोखा (Courier / Customs Scam)",
        "chg": "फर्जी पार्सल अउ कस्टम्स धोखा (Courier Scam)",
        "en": "Fake Courier / Customs Parcel Extortion"
    },
    "lottery_subsidy": {
        "hi": "फर्जी लॉटरी / सरकारी योजना धोखाधड़ी (Lottery / Subsidy Scam)",
        "chg": "फर्जी योजना / लॉटरी के धोखा (Subsidy Scam)",
        "en": "Fake Lottery / Government Subsidy Scam"
    },
    "remote_access": {
        "hi": "रिमोट एक्सेस ऐप धोखा (Remote Access / APK Fraud)",
        "chg": "मोबाइल हैकिंग ऐप धोखा (Remote Access / APK)",
        "en": "Remote Access / APK Fraud"
    },
    "financial_extortion": {
        "hi": "जबरन वसूली / पैसे की मांग (Extortion & Demands)",
        "chg": "जबरन पईसा ऐंठना / वसूली (Extortion)",
        "en": "Financial Extortion & Demand"
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
    "identity_inquiry": {
        "hi": "पहचान व आधिकारिक विवरण पूछताछ (Identity & Branch Verification)",
        "chg": "पहचान व दफ्तर के पूछताछ (Identity Verification)",
        "en": "Caller Identity & Office Verification Inquiry"
    },
    "banking_inquiry": {
        "hi": "सुरक्षित बैंकिंग सेवा पूछताछ (Safe Banking Procedure)",
        "chg": "सुरक्षित बैंक सेवा पूछताछ (Safe Banking)",
        "en": "Safe Banking & Account Service Inquiry"
    },
    "cyber_reporting": {
        "hi": "1930 राष्ट्रीय साइबर हेल्पलाइन व शिकायत सहायता",
        "chg": "1930 साइबर हेल्पलाइन अउ शिकायत मदद",
        "en": "1930 National Cyber Helpline & Complaint Assistance"
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
        "hi": "कॉलर पुलिस/CBI बनकर डिजिटल अरेस्ट की फर्जी धमकी दे रहा है और जमानत या सुरक्षा राशि की मांग कर रहा है। कानून में 'डिजिटल अरेस्ट' नाम की कोई प्रक्रिया नहीं है।",
        "chg": "कॉलर पुलिस बनके 'डिजिटल अरेस्ट' के झूठा डर दिखावत हे अउ जमानत के पईसा मांगत हे। कानून म डिजिटल अरेस्ट नइ होवय।",
        "en": "Extortion attempt: Caller is falsely impersonating law enforcement to extort bail/security money under threat of arrest. Digital arrest does not exist in law."
    },
    "utility_electricity": {
        "hi": "कॉलर बिजली बिल बकाया होने का दावा कर लाइन काटने की धमकी दे रहा है। CSPDCL या बिजली विभाग कभी फोन पर तत्काल लाइन काटने या अनजान नंबर पर पैसे भेजने को नहीं कहता।",
        "chg": "कॉलर बिजली बिल नइ भरे के नाम म लाइन काटे के डर दिखावत हे। बिजली दफ्तर कभू फोन म पईसा पटाए ल नइ कहय।",
        "en": "Caller is falsely threatening power disconnection for unpaid bills. Power companies never demand immediate payments to personal numbers over the phone."
    },
    "courier_customs": {
        "hi": "कॉलर आपके पार्सल में अवैध सामान या ड्रग्स होने का झूठा दावा कर कस्टम्स क्लीयरेंस या पेनल्टी की मांग कर रहा है।",
        "chg": "कॉलर तोर पार्सल म नशीली दवा मिले के झूठा दावा करके टैक्स या पईसा मांगत हे।",
        "en": "Caller falsely claims your package contains contraband to extort clearance fees or penalties under threat."
    },
    "lottery_subsidy": {
        "hi": "कॉलर लॉटरी, कैशबैक या महतारी वंदन/पीएम आवास जैसी योजनाओं का लाभ दिलाने के नाम पर रजिस्ट्रेशन शुल्क या अग्रिम राशि मांग रहा है।",
        "chg": "कॉलर महतारी वंदन या लॉटरी के पईसा दिलाए बर पहिले सत्यापन शुल्क मांगत हे।",
        "en": "Caller promises lottery prizes, cashback, or government welfare subsidies in exchange for registration/processing fees."
    },
    "remote_access": {
        "hi": "कॉलर AnyDesk/QuickSupport ऐप या अज्ञात APK डाउनलोड कराकर आपका फोन हैक करने की कोशिश कर रहा है।",
        "chg": "कॉलर AnyDesk या अनजान APK डाउनलोड करवा के तोर मोबाइल हैक करे के चाल चलत हे।",
        "en": "High risk: Caller is asking to install screen-sharing apps or unknown APK files to compromise your device."
    },
    "financial_extortion": {
        "hi": "कॉलर फर्जी आरोप, बिल या डर दिखाकर तुरंत पैसे ट्रांसफर करने का दबाव बना रहा है।",
        "chg": "कॉलर झूठा आरोप, बिजली बिल या डर दिखा के पईसा ट्रांसफर करवाए के दबाव बनावत हे।",
        "en": "Caller is demanding money or transfers under false pretexts, fake bills, or threats."
    },
    "police_govt_impersonation": {
        "hi": "कॉलर खुद को पुलिस, कस्टम्स या सरकारी अधिकारी बताकर डराने या धमकी देने का प्रयास कर रहा है।",
        "chg": "कॉलर अपन आप ल पुलिस या सरकारी अधिकारी बताके डरवाए के कोसिस करत हे।",
        "en": "Caller is impersonating police, customs, or government authorities to induce panic."
    },
    "bank_impersonation": {
        "hi": "कॉलर बैंक खाता या कार्ड बंद होने का डर दिखाकर दबाव बना रहा है।",
        "chg": "कॉलर तोर बैंक खाता या कार्ड बंद करे के डर दिखा के दबाव बनावत हे।",
        "en": "Caller is using false threats of bank suspension or card blocking to create urgency."
    },
    "moderate_urgency": {
        "hi": "बातचीत में कृत्रिम जल्दबाजी या संस्थागत दावे के संकेत हैं। कृपया सतर्क रहें।",
        "chg": "बातचीत म संदेहास्पद जल्दीबाजी अउ दबाव दिखत हे। सचेत रहव।",
        "en": "Suspicious institutional claims or urgency detected. Proceed with caution."
    },
    "identity_inquiry": {
        "hi": "कॉलर की पहचान, पद या शाखा की पुष्टि की जा रही है। असली अधिकारी अपनी आधिकारिक पहचान और कार्यालय का पता स्पष्ट बताते हैं; जालसाज टालमटोल करते हैं।",
        "chg": "कॉलर के पहचान अउ शाखा के पड़ताल होवत हे। असली अधिकारी सही पता बताथें, ठग मन बहाना बनाथें।",
        "en": "The speaker is inquiring about caller identity or branch credentials. Legitimate officials provide verifiable details; scammers evade verification."
    },
    "banking_inquiry": {
        "hi": "यह बैंक खाते, बैलेंस या सेवाओं से संबंधित सामान्य पूछताछ है। इसमें किसी गोपनीय जानकारी की मांग नहीं है।",
        "chg": "ये बैंक खाता या बैलेंस जांचे के सामान्य बातचीत आय। कोनो गुप्त जानकारी नइ मांगे गे हे।",
        "en": "Standard inquiry regarding banking procedures or balance checks. No suspicious credential solicitation detected."
    },
    "cyber_reporting": {
        "hi": "1930 भारत सरकार की राष्ट्रीय साइबर वित्तीय धोखाधड़ी निवारण हेल्पलाइन है। किसी भी फ्रॉड के शुरुआती 'गोल्डन आवर' में 1930 पर तुरंत कॉल करने से बैंक नोडल अधिकारी द्वारा खाते से निकाली गई राशि को रास्ते में ही फ्रीज कराया जा सकता है।",
        "chg": "1930 भारत सरकार के साइबर ठगी रोके के हेल्पलाइन नंबर आय। ठगी होए के तुरते बाद 1930 म फोन लगाके पईसा रोके जा सकत हे।",
        "en": "1930 is the National Citizen Financial Cyber Fraud Helpline. Calling 1930 within the 'Golden Hour' enables immediate freezing of stolen funds across bank accounts."
    },
    "safe": {
        "hi": "सामान्य बातचीत या पूछताछ। बातचीत में कोई वित्तीय धोखाधड़ी या गुप्त कोड (OTP/PIN) मांगने के संकेत नहीं मिले हैं।",
        "chg": "सामान्य गोठ-बात या सवाल-जवाब। कोनो ठगी, गुप्त कोड या पईसा ऐंठे के संकेत नइ हे।",
        "en": "Normal inquiry or conversation. No financial coercion, credential theft (OTP/PIN), or suspicious threats detected."
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
    "utility_electricity": {
        "hi": "कॉल काटें। किसी भी अनजान नंबर पर पैसे न भेजें। अपने बिजली बिल की स्थिति CSPDCL ऐप या नजदीकी बिजली कार्यालय में जाकर देखें।",
        "chg": "कॉल ल काटव। कोनो अनजान नंबर म पईसा झन भेजव। अपन बिजली दफ्तर जाके पता करव।",
        "en": "Hang up immediately. Never transfer money to numbers given on call. Verify bills only via the official power utility portal."
    },
    "courier_customs": {
        "hi": "कॉल तुरंत डिस्कनेक्ट करें। कोई भी टैक्स या क्लीयरेंस शुल्क न दें। 1930 पर रिपोर्ट दर्ज कराएं।",
        "chg": "कॉल ल तुरते काटव। कोनो क्लीयरेंस फीस झन देहू। 1930 म शिकायत करव।",
        "en": "Disconnect immediately. Do not pay any clearance fees. Report directly to 1930."
    },
    "lottery_subsidy": {
        "hi": "कभी भी सरकारी योजना या लॉटरी पाने के लिए शुल्क न दें। सीधे आधिकारिक सरकारी पोर्टल या पंचायत कार्यालय से संपर्क करें।",
        "chg": "कोनो योजना पाए बर पहिले पईसा झन देहू। सीधा पंचायत या सरकारी दफ्तर म पता करव।",
        "en": "Never pay upfront fees to claim prizes or welfare subsidies. Verify with official government offices."
    },
    "remote_access": {
        "hi": "कोई भी ऐप इंस्टॉल न करें और स्क्रीन शेयर न करें। कॉल तुरंत डिस्कनेक्ट करें।",
        "chg": "कोनो अनजान ऐप डाउनलोड झन करव अउ स्क्रीन शेयर झन करव। फोन ल तुरते काटव।",
        "en": "Do NOT install any APK or screen-sharing app. Disconnect the call right away."
    },
    "financial_extortion": {
        "hi": "पैसे कभी ट्रांसफर न करें। कॉल तुरंत काटें और 1930 पर शिकायत करें।",
        "chg": "कभू पईसा ट्रांसफर झन करव। फोन ल तुरते काटव अउ 1930 म शिकायत करव।",
        "en": "Never send money. Disconnect immediately and file a report with 1930."
    },
    "police_govt_impersonation": {
        "hi": "घबराएं नहीं। फोन काटें और स्थानीय थाने या 1930 हेल्पलाइन पर कॉल कर पुष्टि करें।",
        "chg": "झन डरवाव। फोन काटव अउ अपन नजदीकी थाना या 1930 म पूछ लेवव।",
        "en": "Do not panic. Hang up and verify through official police channels or dial 1930."
    },
    "bank_impersonation": {
        "hi": "किसी अनजान नंबर पर भरोसा न करें। सीधे अपनी बैंक शाखा से संपर्क करें।",
        "chg": "अनजान नंबर म भरोसा झन करव। सीधा अपन बैंक शाखा म जाके पता करव।",
        "en": "Do not trust unsolicited callers. Visit your official bank branch directly."
    },
    "moderate_urgency": {
        "hi": "बातचीत को ध्यान से सुनें। कोई भी निजी कोड, पासवर्ड या पैसे ट्रांसफर न करें।",
        "chg": "गोठ-बात ल ध्यान से सुनव। कोनो गुप्त कोड या पईसा ट्रांसफर झन करव।",
        "en": "Listen carefully. Do not transfer funds or share any personal verification codes."
    },
    "identity_inquiry": {
        "hi": "कॉलर से उनका कर्मचारी आईडी व आधिकारिक ईमेल मांगें। उनके द्वारा दिए गए नंबर के बजाय बैंक की मुख्य वेबसाइट के नंबर पर कॉल करके पुष्टि करें।",
        "chg": "कॉलर ले ओकर आईडी कार्ड मांगव। ओकर देहे नंबर म फोन झन लगाके असली बैंक नंबर म पता करव।",
        "en": "Demand official written communication and employee credentials. Verify independently through official published contact numbers."
    },
    "banking_inquiry": {
        "hi": "हमेशा बैंक के आधिकारिक मोबाइल ऐप, नेट बैंकिंग या बैंक शाखा के आधिकारिक नंबर का ही उपयोग करें।",
        "chg": "हमेशा बैंक के असली मोबाइल ऐप या शाखा म जाके काम करव।",
        "en": "Always use official bank mobile apps or visit your local branch directly for account operations."
    },
    "cyber_reporting": {
        "hi": "तत्काल 1930 डायल करें या cybercrime.gov.in पर शिकायत दर्ज करें। लेनदेन का UTR नंबर, बैंक खाता और स्क्रीनशॉट तैयार रखें।",
        "chg": "तुरते 1930 म फोन लगावव या cybercrime.gov.in म शिकायत दर्ज करव। अपन बैंक पासबुक अउ ट्रांजेक्शन नंबर हाथ म राखव।",
        "en": "Dial 1930 immediately or lodge a report on cybercrime.gov.in. Keep the transaction UTR number and evidence ready."
    },
    "safe": {
        "hi": "सतर्क रहें। अपना OTP या PIN किसी को न बताएं।",
        "chg": "सचेत रहव। अपन OTP या पिन ककरो ले झन बतावव।",
        "en": "Remain cautious. Never share your OTP or PIN with anyone."
    }
}


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
        "utility_electricity": [],
        "police_govt_impersonation": [],
        "courier_customs": [],
        "lottery_subsidy": [],
        "financial_extortion": [],
        "remote_access": [],
        "psychological_manipulation": [],
        "identity_inquiry": [],
        "banking_inquiry": [],
        "cyber_reporting": []
    }

    def check_pats(patterns: List[str], key: str):
        for pat in patterns:
            found = re.findall(pat, full_context_str, re.IGNORECASE)
            if found:
                for f in found:
                    phrase = f if isinstance(f, str) else f[0]
                    if phrase and phrase not in matches[key]:
                        if any(neg in phrase for neg in ["झन बताव", "मत बता", "न बताएं", "never share", "do not share", "झन डार"]):
                            continue
                        matches[key].append(phrase)

    check_pats(CRITICAL_UPI_PIN_PATTERNS, "upi_pin_fraud")
    check_pats(EXPLICIT_OTP_PATTERNS, "otp_fraud")
    check_pats(BANK_IMPERSONATION_PATTERNS, "bank_impersonation")
    check_pats(UTILITY_ELECTRICITY_PATTERNS, "utility_electricity")
    check_pats(POLICE_GOVT_PATTERNS, "police_govt_impersonation")
    check_pats(COURIER_CUSTOMS_PATTERNS, "courier_customs")
    check_pats(LOTTERY_SUBSIDY_PATTERNS, "lottery_subsidy")
    check_pats(FINANCIAL_EXTORTION_PATTERNS, "financial_extortion")
    check_pats(REMOTE_ACCESS_PATTERNS, "remote_access")
    check_pats(PSYCHOLOGICAL_MANIPULATION_PATTERNS, "psychological_manipulation")
    check_pats(IDENTITY_INQUIRY_PATTERNS, "identity_inquiry")
    check_pats(BANKING_INQUIRY_PATTERNS, "banking_inquiry")
    check_pats(CYBER_REPORTING_INQUIRY_PATTERNS, "cyber_reporting")

    # Step 3: Determine Risk Level & Primary Category
    risk_level = "LOW"
    confidence = 0.95

    # Safe override if user was only narrating Swiggy/passbook and no attack patterns
    has_attacks = any(len(matches[k]) > 0 for k in [
        "upi_pin_fraud", "otp_fraud", "police_govt_impersonation",
        "financial_extortion", "remote_access", "utility_electricity",
        "courier_customs", "lottery_subsidy"
    ])

    if (is_genuine_alert or is_user_narration) and not has_attacks:
        return {
            "risk_level": "LOW",
            "is_scam": False,
            "scam_category": "सुरक्षित संदेश / सामान्य बातचीत",
            "scam_category_hi": "सुरक्षित संदेश / सामान्य बातचीत",
            "scam_category_chg": "सुरक्षित संदेश / सामान्य बातचीत",
            "scam_category_en": "Safe / Normal Conversation (No Threat Detected)",
            "reason": "यह एक सामान्य बातचीत या सुरक्षा चेतावनी है। किसी गुप्त कोड की मांग नहीं की गई है।",
            "reason_hi": "यह एक सामान्य बातचीत या सुरक्षा चेतावनी है। किसी गुप्त कोड की मांग नहीं की गई है।",
            "reason_chg": "ये सामान्य बातचीत आय। कोनो गुप्त कोड या पईसा नइ मांगे गे हे।",
            "reason_en": "Normal conversation or genuine security notice. No confidential codes solicited.",
            "recommended_action": "सतर्क रहें। अपना OTP या PIN किसी को न बताएं।",
            "recommended_action_hi": "सतर्क रहें। अपना OTP या PIN किसी को न बताएं।",
            "recommended_action_chg": "सचेत रहव। अपन OTP या पिन ककरो ले झन बतावव।",
            "recommended_action_en": "Remain cautious. Never share your OTP or PIN with anyone.",
            "suspicious_phrases": [],
            "matched_categories": [],
            "confidence": 0.98,
            "certainty": "High Confidence"
        }

    # Category & Explanation Dictionaries for Multi-lingual Localization
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
    elif (len(matches["police_govt_impersonation"]) > 0 and (len(matches["financial_extortion"]) > 0 or any(k in text_lower for k in ["arrest", "jail", "warrant", "fine", "bail", "money", "transfer"]))) or any(k in text_lower for k in ["digital arrest", "digital_arrest"]):
        risk_level = "CRITICAL"
        eval_key = "digital_arrest"
        confidence = 0.98
    elif len(matches["remote_access"]) > 0:
        risk_level = "HIGH"
        eval_key = "remote_access"
        confidence = 0.95
    elif len(matches["utility_electricity"]) > 0:
        risk_level = "HIGH"
        eval_key = "utility_electricity"
        confidence = 0.95
    elif len(matches["courier_customs"]) > 0:
        risk_level = "HIGH"
        eval_key = "courier_customs"
        confidence = 0.94
    elif len(matches["lottery_subsidy"]) > 0:
        risk_level = "HIGH"
        eval_key = "lottery_subsidy"
        confidence = 0.93
    elif len(matches["financial_extortion"]) > 0:
        risk_level = "HIGH"
        eval_key = "financial_extortion"
        confidence = 0.94
    elif len(matches["police_govt_impersonation"]) > 0:
        risk_level = "HIGH"
        eval_key = "police_govt_impersonation"
        confidence = 0.92
    elif len(matches["bank_impersonation"]) > 0 and (
        len(matches["psychological_manipulation"]) > 0 or 
        any(k in full_context_str for k in ["block", "suspend", "band", "freeze", "kyc", "yono", "बंद", "ब्लॉक", "सील"])
    ):
        risk_level = "HIGH"
        eval_key = "bank_impersonation"
        confidence = 0.91
    elif len(matches["bank_impersonation"]) > 0 or len(matches["psychological_manipulation"]) > 0:
        risk_level = "MODERATE"
        eval_key = "moderate_urgency"
        confidence = 0.78
    elif len(matches["identity_inquiry"]) > 0:
        risk_level = "LOW"
        eval_key = "identity_inquiry"
        confidence = 0.95
    elif len(matches["banking_inquiry"]) > 0:
        risk_level = "LOW"
        eval_key = "banking_inquiry"
        confidence = 0.95
    elif len(matches["cyber_reporting"]) > 0:
        risk_level = "LOW"
        eval_key = "cyber_reporting"
        confidence = 0.98
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

    # Audio warning text generation (Hindi, Chhattisgarhi & English)
    audio_warning_hi = ""
    audio_warning_en = ""
    audio_warning_chg = ""
    if risk_level == "CRITICAL":
        if "upi_pin_fraud" in active_categories:
            audio_warning_hi = "सावधान! किसी को भी अपना UPI पिन न बताएं और न ही दर्ज करें। पैसे पाने के लिए पिन की जरूरत नहीं होती।"
            audio_warning_chg = "भारी खतरा! कॉलर तोर से UPI पिन मांगे के चाल चलत हे। कभू पिन झन डारव।"
            audio_warning_en = "Warning! Never enter or disclose your UPI PIN. UPI PIN is never needed to receive money."
        else:
            audio_warning_hi = "सावधान! किसी को भी अपना OTP या बैंक कोड न बताएं। कॉल तुरंत काटें।"
            audio_warning_chg = "सावधान! तोर गुप्त OTP ककरो ले झन बतावव। फोन ल तुरते काटव।"
            audio_warning_en = "Alert! Never share your OTP or bank codes. Hang up the call immediately."
    elif risk_level == "HIGH":
        if "remote_access" in active_categories:
            audio_warning_hi = "सतर्क रहें! कोई भी ऐप या APK डाउनलोड न करें। यह ठगी का प्रयास हो सकता है।"
            audio_warning_chg = "सतर्क रहव! कोनो अनजान ऐप डाउनलोड झन करव अउ स्क्रीन शेयर झन करव।"
            audio_warning_en = "Caution! Do not install any app or APK. This may be a fraudulent attempt."
        elif "financial_extortion" in active_categories:
            audio_warning_hi = "चेतावनी! किसी अनजान को पैसे या ऑनलाइन ट्रांसफर न करें। कॉल तुरंत काटें।"
            audio_warning_chg = "चेतावनी! ककरो बहकावे म आके पईसा ट्रांसफर झन करव। कॉल तुरते काटव।"
            audio_warning_en = "Warning! Do not transfer money or pay any caller. Disconnect immediately."
        else:
            audio_warning_hi = "सतर्क रहें! पुलिस या बैंक कभी फोन पर पैसे या गिरफ्तारी की धमकी नहीं देते।"
            audio_warning_chg = "झन डरवाव! फर्जी पुलिस या डिजिटल अरेस्ट के धमकी म झन आवव। फोन काटव।"
            audio_warning_en = "Be cautious! Official authorities never threaten arrest or demand money over the phone."
    elif risk_level == "MODERATE":
        audio_warning_hi = "ध्यान दें! बातचीत संदिग्ध लग रही है। कोई भी गोपनीय जानकारी न दें।"
        audio_warning_chg = "सचेत रहव! गोठ-बात संदेहास्पद लगत हे। कोनो गुप्त जानकारी झन देवव।"
        audio_warning_en = "Notice! Conversation seems suspicious. Do not share confidential information."

    return {
        "eval_key": eval_key,
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
        "audio_warning_chg": audio_warning_chg,
        "audio_warning_en": audio_warning_en,
        "suspicious_phrases": list(set(suspicious_phrases)),
        "matched_categories": active_categories,
        "confidence": confidence,
        "certainty": f"{int(confidence * 100)}% Certainty"
    }
