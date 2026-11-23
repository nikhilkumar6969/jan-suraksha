"""
Official Communication Verification Engine (OCVE)
Suraksha — Offline-First Multi-Pillar Communication Auditing Layer

CRITICAL MANDATES:
1. Complements the existing ML model (scam_model.joblib) without replacing or altering it.
2. NEVER declares any communication 100% genuine, authentic, or safe.
3. Provides evidence-based status classifications:
   - "Consistent with verified communication patterns"
   - "Suspicious communication patterns detected"
   - "Potential impersonation detected"
   - "Insufficient information to verify"
4. Evaluates four independent verification pillars with transparent reporting of unavailable context.
5. Multilingual explanations across English, Hindi, and Hinglish / Chhattisgarhi.
"""

import re
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple

try:
    from app.detect.trai_header import (
        parse_sender_id,
        load_headers_registry,
        extract_domains_from_text,
        KNOWN_SHORTENERS,
        FINANCIAL_CLAIM_KEYWORDS,
        URGENCY_KEYWORDS,
        APK_DOWNLOAD_KEYWORDS,
        levenshtein_distance
    )
    from app.detect.lookalike import detect_lookalikes_in_text
    from app.detect.reputation import check_reputation
except ImportError:
    from backend.app.detect.trai_header import (
        parse_sender_id,
        load_headers_registry,
        extract_domains_from_text,
        KNOWN_SHORTENERS,
        FINANCIAL_CLAIM_KEYWORDS,
        URGENCY_KEYWORDS,
        APK_DOWNLOAD_KEYWORDS,
        levenshtein_distance
    )
    from backend.app.detect.lookalike import detect_lookalikes_in_text
    from backend.app.detect.reputation import check_reputation


class EvidenceStatus(str, Enum):
    """Evidence-based classification standards (Never binary 100% safe/authentic)."""
    CONSISTENT = "Consistent with verified communication patterns"
    SUSPICIOUS = "Suspicious communication patterns detected"
    POTENTIAL_IMPERSONATION = "Potential impersonation detected"
    INSUFFICIENT_INFO = "Insufficient information to verify"


# Multilingual Labels and Disclaimers
STATUS_TRANSLATIONS = {
    "en": {
        EvidenceStatus.CONSISTENT.value: "Consistent with verified communication patterns",
        EvidenceStatus.SUSPICIOUS.value: "Suspicious communication patterns detected",
        EvidenceStatus.POTENTIAL_IMPERSONATION.value: "Potential impersonation detected",
        EvidenceStatus.INSUFFICIENT_INFO.value: "Insufficient information to verify",
    },
    "hi": {
        EvidenceStatus.CONSISTENT.value: "सत्यापित संचार पैटर्न के अनुरूप (सतर्कता आवश्यक)",
        EvidenceStatus.SUSPICIOUS.value: "संदेहास्पद संचार पैटर्न की पहचान हुई",
        EvidenceStatus.POTENTIAL_IMPERSONATION.value: "संभावित प्रतिरूपण (पहचान की चोरी/धोखाधड़ी) का पता चला",
        EvidenceStatus.INSUFFICIENT_INFO.value: "सत्यापन के लिए अपर्याप्त जानकारी उपलब्ध",
    },
    "chg": {
        EvidenceStatus.CONSISTENT.value: "सत्यापित संदेश ढांचा जइसन दिखत हे (सचेत रहव)",
        EvidenceStatus.SUSPICIOUS.value: "शंकास्पद संचार पैटर्न दिखे हे",
        EvidenceStatus.POTENTIAL_IMPERSONATION.value: "संभावित फर्जी पहचान / नकल के खतरा",
        EvidenceStatus.INSUFFICIENT_INFO.value: "जांच बर जरूरी जानकारी नइ हे",
    }
}

SECURITY_DISCLAIMERS = {
    "en": (
        "Zero-Trust Security Notice: Even when message formatting and sender IDs match legitimate patterns, "
        "telecom channels do not provide end-to-end cryptographic proof to user devices. Never treat any message "
        "as 100% safe. Do not share OTPs, PINs, or passwords with anyone under any circumstances."
    ),
    "hi": (
        "जीरो-ट्रस्ट सुरक्षा सूचना: यद्यपि संदेश का प्रारूप और प्रेषक आईडी आधिकारिक पैटर्न के अनुरूप है, "
        "किन्तु दूरसंचार माध्यम उपयोगकर्ता उपकरण को एंड-टू-एंड क्रिप्टोग्राफिक प्रमाण प्रदान नहीं करते। "
        "किसी भी संदेश को 100% सुरक्षित न मानें। किसी भी परिस्थिति में अपना OTP, UPI पिन या पासवर्ड साझा न करें।"
    ),
    "chg": (
        "सुरक्षा सूचना: संदेश के लिखावट असली जइसन दिखे के बाद घलो एकर 100% सुरक्षित होए के पक्का गारंटी नइ होवय। "
        "ककरो ले अपन OTP, UPI पिन या बैंक पासवर्ड कभू शेयर झन करव।"
    )
}

RECOMMENDATIONS = {
    "en": {
        "consistent": [
            "Verify transactions directly within your official banking app or physical passbook.",
            "Remember that genuine banks, DISCOMs, and government bodies NEVER request your OTP or UPI PIN to receive money.",
            "Do not click unsolicited links or download attachments received in messages."
        ],
        "suspicious": [
            "Do not call phone numbers or click web links contained inside this message.",
            "Contact the official customer care helpline published on your physical bank card or official utility bill.",
            "If pressured with immediate account blocking or power disconnection, verify directly at your local branch."
        ],
        "impersonation": [
            "Do not respond to or engage with this sender. Authentic institutions do not use personal mobile numbers for official alerts.",
            "Do not download any APK files or grant remote screen control (e.g. AnyDesk, TeamViewer).",
            "Report this incident immediately to the National Cyber Crime Helpline at 1930 or cybercrime.gov.in."
        ],
        "insufficient": [
            "The message provides insufficient context or verifiable identifiers to confirm its source.",
            "Treat all unknown communications with caution and avoid acting on urgency claims.",
            "Seek manual confirmation from the supposed institution through an independent, trusted channel."
        ]
    },
    "hi": {
        "consistent": [
            "लेन-देन की पुष्टि सीधे अपने आधिकारिक बैंक ऐप या पासबुक से करें।",
            "याद रखें कि असली बैंक, बिजली विभाग या सरकार कभी पैसे देने के लिए OTP या UPI पिन नहीं मांगते।",
            "संदेश में आए किसी भी लिंक पर बिना पुष्टि के क्लिक न करें।"
        ],
        "suspicious": [
            "इस संदेश में दिए गए किसी भी फोन नंबर पर कॉल न करें और न ही किसी लिंक पर क्लिक करें।",
            "अपने बैंक कार्ड या मूल बिजली बिल पर छपे आधिकारिक हेल्पलाइन नंबर पर ही संपर्क करें।",
            "खाता बंद होने या बिजली कटने की धमकी मिलने पर सीधे स्थानीय शाखा या दफ्तर जाकर पुष्टि करें।"
        ],
        "impersonation": [
            "इस प्रेषक के संदेश का जवाब न दें। असली संस्थाएं आधिकारिक सूचनाओं के लिए साधारण 10-अंकों के मोबाइल नंबर का उपयोग नहीं करतीं।",
            "कोई भी APK ऐप डाउनलोड न करें और न ही स्क्रीन शेयरिंग (AnyDesk, TeamViewer) की अनुमति दें।",
            "इस धोखाधड़ी की तुरंत राष्ट्रीय साइबर अपराध हेल्पलाइन 1930 या cybercrime.gov.in पर रिपोर्ट करें।"
        ],
        "insufficient": [
            "संदेश में स्रोत की पुष्टि करने के लिए पर्याप्त विवरण या सत्यापित पहचानकर्ता मौजूद नहीं हैं।",
            "अज्ञात संदेशों के प्रति सतर्क रहें और किसी भी तात्कालिक दबाव में आकर कोई कार्रवाई न करें।",
            "संबंधित संस्था से उनके आधिकारिक व स्वतंत्र माध्यम द्वारा संपर्क करके पुष्टि करें।"
        ]
    },
    "chg": {
        "consistent": [
            "अपन बैंक खाता के जांच सीधे बैंक जाके या असली ऐप ले करव।",
            "सुरक्षा नियम: असली बैंक या बिजली दफ्तर कभू पइसा पाए बर OTP या UPI पिन नइ मांगंय।",
            "कोनो अनजान लिंक ल छुवव झन।"
        ],
        "suspicious": [
            "ए मैसेज म देहे कोनो फोन नंबर म फोन झन लगावव।",
            "अपन बिजली बिल या पासबुक म लिखे सरकारी नंबर म ही बात करव।",
            "बिजली काटे के धमकी मिले म अपन बिजली दफ्तर जाके पता करव।"
        ],
        "impersonation": [
            "ए नंबर म कोनो जवाब झन देबो। असली बैंक साधारण 10-अंक वाले मोबाइल नंबर ले मैसेज नइ भेजंय।",
            "कोनो अनजान ऐप डाउनलोड झन करव अउ न ही AnyDesk चालू करव।",
            "तुरंत साइबर हेल्पलाइन 1930 म फोन लगाके शिकायत दर्ज कराव।"
        ],
        "insufficient": [
            "ए संदेश म जांच करे बर पूरा जानकारी नइ हे।",
            "अनजान संदेश ले सचेत रहव अउ हड़बड़ी म कोनो काम झन करव।",
            "अपन बैंक या दफ्तर जाके सीधा पूछ-परख करव।"
        ]
    }
}


def evaluate_sender_pillar(
    sender: Optional[str],
    text: str,
    user_lang: str = "hi"
) -> Dict[str, Any]:
    """
    Pillar 1: Sender & Channel Authenticity
    Audits TRAI DLT registration, operator prefixes, 10-digit mobile smishing,
    and flags that SMS sender IDs are subject to telecom spoofing risks.
    """
    lang = user_lang if user_lang in STATUS_TRANSLATIONS else "hi"

    if not sender or not sender.strip():
        return {
            "pillar_name": "Sender & Channel Authenticity",
            "status": EvidenceStatus.INSUFFICIENT_INFO.value,
            "status_localized": STATUS_TRANSLATIONS[lang][EvidenceStatus.INSUFFICIENT_INFO.value],
            "risk_level": "NEUTRAL",
            "score": 0.50,
            "indicators_present": ["Sender ID not provided / unavailable in input"],
            "indicators_absent": ["TRAI DLT Header", "Telecom Carrier Signature"],
            "verified_facts": ["No sender identifier supplied to evaluate."],
            "spoofing_vulnerability": "High: Unknown sender source cannot be evaluated against operator registries.",
            "reason": (
                "Sender ID was not provided. Without sender metadata, carrier-level registration "
                "cannot be audited." if lang == "en" else
                "प्रेषक आईडी उपलब्ध नहीं कराई गई है। प्रेषक के बिना दूरसंचार पंजीकरण की पुष्टि संभव नहीं है।"
            )
        }

    parsed = parse_sender_id(sender)
    registry = load_headers_registry()
    brands = registry.get("brands", [])

    body_clean = text or ""
    has_financial_claim = any(re.search(pat, body_clean, re.IGNORECASE) for pat in FINANCIAL_CLAIM_KEYWORDS)

    # 1. Personal 10-digit mobile number
    if parsed["is_mobile"]:
        if has_financial_claim:
            status = EvidenceStatus.POTENTIAL_IMPERSONATION.value
            risk_level = "CRITICAL"
            score = 0.95
            reason = (
                f"SMS originated from a personal 10-digit mobile number (+91-{parsed['mobile_number']}) "
                f"while communicating official banking, utility, or government claims. Genuine institutions "
                f"use registered alphanumeric TRAI headers, never personal SIM cards." if lang == "en" else
                f"संदेश व्यक्तिगत 10-अंकों के मोबाइल नंबर (+91-{parsed['mobile_number']}) से भेजा गया है, जबकि इसमें "
                f"बैंक/बिजली/सरकारी दावे किए गए हैं। असली संस्थाएं कभी साधारण मोबाइल नंबर से आधिकारिक संदेश नहीं भेजतीं।"
            )
        else:
            status = EvidenceStatus.SUSPICIOUS.value
            risk_level = "MEDIUM"
            score = 0.40
            reason = (
                f"Message received from a personal 10-digit mobile number (+91-{parsed['mobile_number']}). "
                f"Official transactional communication must originate from commercial DLT headers." if lang == "en" else
                f"व्यक्तिगत 10-अंकों के मोबाइल नंबर (+91-{parsed['mobile_number']}) से संदेश प्राप्त हुआ।"
            )

        return {
            "pillar_name": "Sender & Channel Authenticity",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": [f"10-Digit Mobile Sender (+91-{parsed['mobile_number']})"],
            "indicators_absent": ["Commercial TRAI DLT Header", "Institutional Sender ID"],
            "verified_facts": [f"Originating address parsed as personal mobile number: {parsed['mobile_number']}."],
            "spoofing_vulnerability": "High: Personal SIMs lack institutional DLT authentication.",
            "reason": reason
        }

    # 2. TRAI Header Check against Registry
    header_cand = parsed["header"]
    matched_brand = None
    exact_match = False

    for b in brands:
        registered = b.get("headers") or b.get("registered_headers", [])
        if header_cand in registered:
            exact_match = True
            matched_brand = b
            break

    # Lookalike header check if no exact match
    lookalike_found = None
    if not exact_match and len(header_cand) >= 4:
        for b in brands:
            brand_title = b.get("brand") or b.get("brand_name", "Unknown Brand")
            registered = b.get("headers") or b.get("registered_headers", [])
            for reg_h in registered:
                dist = levenshtein_distance(header_cand, reg_h)
                if dist in (1, 2) and len(reg_h) >= 4:
                    lookalike_found = {"brand": brand_title, "official_header": reg_h, "distance": dist}
                    break
            if lookalike_found:
                break

    if lookalike_found:
        status = EvidenceStatus.POTENTIAL_IMPERSONATION.value
        risk_level = "CRITICAL"
        score = 0.96
        reason = (
            f"Sender header '{header_cand}' is a deceptive lookalike of official header "
            f"'{lookalike_found['official_header']}' ({lookalike_found['brand']})." if lang == "en" else
            f"प्रेषक हेडर '{header_cand}' असली हेडर '{lookalike_found['official_header']}' "
            f"({lookalike_found['brand']}) का मिलता-जुलता नकल (टायपोस्कॉटिंग) है।"
        )
        return {
            "pillar_name": "Sender & Channel Authenticity",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": [f"Deceptive Lookalike Header: {header_cand} -> {lookalike_found['official_header']}"],
            "indicators_absent": ["Official Registry Match"],
            "verified_facts": [f"Header '{header_cand}' does not match registered DLT principal entities."],
            "spoofing_vulnerability": "Critical: Impersonation attempt detected via lookalike header.",
            "reason": reason
        }

    if exact_match and matched_brand:
        brand_title = matched_brand.get("brand") or matched_brand.get("brand_name", "Institutional Sender")
        status = EvidenceStatus.CONSISTENT.value
        risk_level = "LOW"
        score = 0.10
        reason = (
            f"Header '{header_cand}' matches registered DLT principal entity: {brand_title}. "
            f"Consistent with verified patterns, though SMS headers remain vulnerable to carrier-level spoofing." if lang == "en" else
            f"प्रेषक हेडर '{header_cand}' पंजीकृत DLT संस्थान ({brand_title}) के अनुरूप है। "
            f"यह वैध पैटर्न के समान है, किन्तु दूरसंचार हेडर स्पूफिंग के जोखिम से पूर्णतः मुक्त नहीं होते।"
        )
        return {
            "pillar_name": "Sender & Channel Authenticity",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": [f"Registered TRAI DLT Header: {header_cand} ({brand_title})"],
            "indicators_absent": ["Deceptive Lookalike Mismatch", "10-Digit Mobile Origin"],
            "verified_facts": [
                f"Header '{header_cand}' is registered to {brand_title}.",
                f"Operator prefix: {parsed['operator_prefix'] or 'Standard'}"
            ],
            "spoofing_vulnerability": "Moderate: Format matches legitimate sender, but client cannot cryptographically authenticate telecom transmission.",
            "reason": reason
        }

    # Unregistered alphanumeric header
    status = EvidenceStatus.INSUFFICIENT_INFO.value
    risk_level = "MEDIUM"
    score = 0.45
    reason = (
        f"Sender header '{header_cand}' is not listed in the verified institutional DLT registry. "
        f"It may be a regional, private, or promotional sender." if lang == "en" else
        f"प्रेषक हेडर '{header_cand}' स्थानीय सत्यापित DLT रजिस्ट्री में दर्ज नहीं है।"
    )
    return {
        "pillar_name": "Sender & Channel Authenticity",
        "status": status,
        "status_localized": STATUS_TRANSLATIONS[lang][status],
        "risk_level": risk_level,
        "score": score,
        "indicators_present": [f"Unregistered Header: {header_cand}"],
        "indicators_absent": ["Verified DLT Registry Match"],
        "verified_facts": [f"Header format: Alphanumeric {len(header_cand)} chars."],
        "spoofing_vulnerability": "High: Unverified sender origin.",
        "reason": reason
    }


def evaluate_url_pillar(
    text: str,
    sender: Optional[str] = None,
    user_lang: str = "hi"
) -> Dict[str, Any]:
    """
    Pillar 2: URL & Domain Integrity
    Audits embedded hyperlinks, lookalike domains, shorteners,
    reputation blacklist matches, and domain-brand alignment.
    """
    lang = user_lang if user_lang in STATUS_TRANSLATIONS else "hi"
    extracted = extract_domains_from_text(text)
    lookalike_findings = detect_lookalikes_in_text(text)
    rep_match = check_reputation(text)

    if not extracted:
        return {
            "pillar_name": "URL & Domain Integrity",
            "status": EvidenceStatus.CONSISTENT.value,
            "status_localized": STATUS_TRANSLATIONS[lang][EvidenceStatus.CONSISTENT.value],
            "risk_level": "LOW",
            "score": 0.05,
            "indicators_present": [],
            "indicators_absent": ["Suspicious Links", "Lookalike Domains", "URL Shorteners"],
            "verified_facts": ["No embedded hyperlinks or web addresses detected in message body."],
            "unavailable_context": "Destination server infrastructure telemetry not applicable.",
            "reason": (
                "No hyperlinks detected in message text. Absence of links reduces direct phishing exposure." if lang == "en" else
                "संदेश में कोई वेब लिंक या यूआरएल नहीं पाया गया। लिंक न होने से फिशिंग का प्रत्यक्ष जोखिम कम होता है।"
            )
        }

    # Check for confirmed reputation blacklist match
    if rep_match and rep_match.get("is_known_scam"):
        status = EvidenceStatus.SUSPICIOUS.value
        risk_level = "CRITICAL"
        score = 0.99
        matched_ind = rep_match.get("matched_indicator", "")
        reason = (
            f"Critical Security Alert: Domain or indicator '{matched_ind}' matches a confirmed entry "
            f"in the cryptographically signed offline fraud blacklist." if lang == "en" else
            f"अत्यंत गंभीर सुरक्षा चेतावनी: लिंक '{matched_ind}' सत्यापित साइबर सुरक्षा ब्लैकलिस्ट में दर्ज ठग का है।"
        )
        return {
            "pillar_name": "URL & Domain Integrity",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": [f"Blacklisted Fraud Indicator: {matched_ind}"],
            "indicators_absent": ["Verified Official Domain"],
            "verified_facts": [f"Indicator '{matched_ind}' flagged by offline threat intelligence."],
            "unavailable_context": "Host server hosting provider logs not directly inspectable offline.",
            "reason": reason
        }

    # Check for homoglyph / typosquatting lookalike domains
    if lookalike_findings:
        status = EvidenceStatus.POTENTIAL_IMPERSONATION.value
        risk_level = "CRITICAL"
        score = 0.98
        first_finding = lookalike_findings[0]
        detected_dom = first_finding.get("detected_domain", "")
        target_brand = first_finding.get("target_brand", "official brand")
        reason = (
            f"Deceptive lookalike domain detected: '{detected_dom}' is an imitation of {target_brand}. "
            f"Scammers register typosquatting domains to harvest credentials." if lang == "en" else
            f"फर्जी वेबसाइट (लुकअलाइक) की पहचान: '{detected_dom}' संस्था ({target_brand}) की नकल है।"
        )
        return {
            "pillar_name": "URL & Domain Integrity",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": [f"Typosquatting/Homoglyph Domain: {detected_dom} -> {target_brand}"],
            "indicators_absent": ["Official Domain Match"],
            "verified_facts": [f"Domain '{detected_dom}' targets brand '{target_brand}'."],
            "unavailable_context": "WHOIS registrant identity hidden behind privacy proxy.",
            "reason": reason
        }

    # Check for URL shorteners
    shorteners_found = [dom for _, dom in extracted if any(dom == s or dom.endswith("." + s) for s in KNOWN_SHORTENERS)]
    if shorteners_found:
        status = EvidenceStatus.SUSPICIOUS.value
        risk_level = "HIGH"
        score = 0.80
        reason = (
            f"Obfuscated link detected via URL shortener ({', '.join(shorteners_found)}). "
            f"Official entities avoid third-party link shorteners for transactional security." if lang == "en" else
            f"संदेश में लिंक छिपाने वाला शॉर्टनर ({', '.join(shorteners_found)}) पाया गया। "
            f"आधिकारिक संस्थाएं सुरक्षा कारणों से ऐसे शॉर्टनर का उपयोग नहीं करतीं।"
        )
        return {
            "pillar_name": "URL & Domain Integrity",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": [f"URL Shortener: {', '.join(shorteners_found)}"],
            "indicators_absent": ["Direct Transparent URL"],
            "verified_facts": [f"Shortener domain detected: {shorteners_found[0]}."],
            "unavailable_context": "Final destination redirect target cannot be evaluated without online resolution.",
            "reason": reason
        }

    # Check alignment against registered brand domains if sender is known
    registry = load_headers_registry()
    matched_brand = None
    if sender:
        parsed_s = parse_sender_id(sender)
        h = parsed_s["header"]
        for b in registry.get("brands", []):
            registered = b.get("headers") or b.get("registered_headers", [])
            if h in registered:
                matched_brand = b
                break

    domains_in_text = [dom for _, dom in extracted]
    if matched_brand:
        brand_title = matched_brand.get("brand") or matched_brand.get("brand_name", "Official Brand")
        official_domains = matched_brand.get("domains") or matched_brand.get("official_domains", [])
        aligned = any(
            any(dom == od or dom.endswith("." + od) for od in official_domains)
            for dom in domains_in_text
        )
        if aligned:
            status = EvidenceStatus.CONSISTENT.value
            risk_level = "LOW"
            score = 0.15
            reason = (
                f"Domain '{domains_in_text[0]}' matches official domain registry for {brand_title}. "
                f"Matches authentic patterns, though TLS certificate integrity must be validated in browser." if lang == "en" else
                f"वेबसाइट '{domains_in_text[0]}' संस्थान ({brand_title}) की आधिकारिक सूची में दर्ज है।"
            )
        else:
            status = EvidenceStatus.POTENTIAL_IMPERSONATION.value
            risk_level = "HIGH"
            score = 0.90
            reason = (
                f"Domain mismatch: Sender header claims {brand_title}, but the link points to "
                f"unaffiliated domain '{domains_in_text[0]}'. Official domains: {', '.join(official_domains)}." if lang == "en" else
                f"डोमेन बेमेल: संदेश {brand_title} का दावा करता है, परन्तु लिंक असंबद्ध वेबसाइट "
                f"'{domains_in_text[0]}' का दिया गया है।"
            )
        return {
            "pillar_name": "URL & Domain Integrity",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": [f"Domain: {domains_in_text[0]}"],
            "indicators_absent": [] if aligned else [f"Official Brand Domain ({', '.join(official_domains)})"],
            "verified_facts": [f"Domain extracted: {domains_in_text[0]}"],
            "unavailable_context": "Live SSL/TLS certificate validity not checked offline.",
            "reason": reason
        }

    # General domain without known brand
    status = EvidenceStatus.INSUFFICIENT_INFO.value
    risk_level = "MEDIUM"
    score = 0.45
    reason = (
        f"Domain '{domains_in_text[0]}' is present in text without an official brand registry link to confirm ownership." if lang == "en" else
        f"संदेश में दिया गया लिंक '{domains_in_text[0]}' किसी सत्यापित सरकारी/बैंक रजिस्ट्री से लिंक नहीं है।"
    )
    return {
        "pillar_name": "URL & Domain Integrity",
        "status": status,
        "status_localized": STATUS_TRANSLATIONS[lang][status],
        "risk_level": risk_level,
        "score": score,
        "indicators_present": [f"Unverified Domain: {domains_in_text[0]}"],
        "indicators_absent": ["Verified Institutional Affiliation"],
        "verified_facts": [f"Domain parsed: {domains_in_text[0]}"],
        "unavailable_context": "Live DNS record and domain age not checked in offline mode.",
        "reason": reason
    }


def evaluate_security_demands_pillar(
    text: str,
    user_lang: str = "hi"
) -> Dict[str, Any]:
    """
    Pillar 3: Security & Credential Demands
    Audits whether the message demands sensitive credentials (OTP, PIN, passwords),
    remote access APK installations, or asserts coercive urgency.
    """
    lang = user_lang if user_lang in STATUS_TRANSLATIONS else "hi"
    text_clean = text or ""

    # Explicit OTP / PIN demand pattern
    otp_demand_patterns = [
        r"(?:share|send|tell|give|enter)\s+(?:your\s+)?(?:otp|pin|password|cvv)",
        r"(?:ओटीपी|पिन|पासवर्ड|सीवीवी)\s*(?:शेयर|भेजें|बताएं|दर्ज)",
        r"(?:otp|pin)\s+(?:batao|bhejo|share\s*karo)"
    ]
    is_otp_demanded = any(re.search(pat, text_clean, re.IGNORECASE) for pat in otp_demand_patterns)

    # Genuine bank warning ("DO NOT SHARE WITH ANYONE")
    genuine_warning_patterns = [
        r"do\s*not\s*share\s*(?:this|it|otp|with\s*anyone)?",
        r"(?:किसी\s*के\s*साथ|ककरो\s*ले)\s*(?:शेयर\s*न\s*करें|साझा\s*न\s*करें|बताव\s*झन)",
        r"never\s*share",
        r"kisi\s*ko\s*mat\s*dena"
    ]
    has_genuine_warning = any(re.search(pat, text_clean, re.IGNORECASE) for pat in genuine_warning_patterns)

    # APK / Remote Access demands
    has_apk_demand = any(re.search(pat, text_clean, re.IGNORECASE) for pat in APK_DOWNLOAD_KEYWORDS)

    # Coercive urgency
    has_coercive_urgency = any(re.search(pat, text_clean, re.IGNORECASE) for pat in URGENCY_KEYWORDS)

    # Prohibited credential theft demand
    if is_otp_demanded:
        status = EvidenceStatus.SUSPICIOUS.value
        risk_level = "CRITICAL"
        score = 0.98
        reason = (
            "Prohibited security request: The message explicitly demands your secret OTP, PIN, or password. "
            "Legitimate institutions, banks, and telecom providers NEVER ask users to share OTPs." if lang == "en" else
            "प्रतिबंधित सुरक्षा मांग: संदेश में आपका गुप्त OTP, पिन या पासवर्ड मांगा गया है। "
            "कोई भी असली बैंक या संस्था कभी भी फोन या मैसेज पर OTP नहीं मांगती।"
        )
        return {
            "pillar_name": "Security & Credential Demands",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": ["Explicit OTP / PIN Solicitation"],
            "indicators_absent": ["Adherence to Banking Non-Disclosure Standard"],
            "verified_facts": ["Direct credential request detected in text syntax."],
            "unavailable_context": "Intent of recipient's active session cannot be verified.",
            "reason": reason
        }

    # Malicious APK / Remote tool demand
    if has_apk_demand:
        status = EvidenceStatus.SUSPICIOUS.value
        risk_level = "CRITICAL"
        score = 0.95
        reason = (
            "Prohibited application download request: The message asks to install an external APK or screen-sharing "
            "tool (e.g. AnyDesk, QuickSupport). This tactic grants scammers full remote control of your device." if lang == "en" else
            "असुरक्षित ऐप डाउनलोड का अनुरोध: संदेश में अज्ञात APK ऐप या स्क्रीन शेयरिंग सॉफ्टवेयर डाउनलोड करने को "
            "कहा गया है। इससे जालसाज आपके पूरे फोन पर नियंत्रण पा सकते हैं।"
        )
        return {
            "pillar_name": "Security & Credential Demands",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": ["Third-Party APK / Remote Access Tool Demand"],
            "indicators_absent": ["Official App Store Distribution"],
            "verified_facts": ["Request to install unverified software detected."],
            "unavailable_context": "File hash and virus signature of the remote APK unavailable offline.",
            "reason": reason
        }

    # Authentic safety advisory present
    if has_genuine_warning and not is_otp_demanded:
        status = EvidenceStatus.CONSISTENT.value
        risk_level = "LOW"
        score = 0.10
        reason = (
            "Adheres to security advisory standards: The message includes an explicit warning "
            "('Do not share with anyone'). This is consistent with genuine transactional security alerts." if lang == "en" else
            "सुरक्षा सलाह मानकों के अनुरूप: संदेश में स्पष्ट रूप से 'OTP किसी के साथ साझा न करें' जैसी "
            "चेतावनी शामिल है, जो कि वास्तविक बैंक सुरक्षा संदेशों का मानक नियम है।"
        )
        return {
            "pillar_name": "Security & Credential Demands",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": ["Explicit Non-Disclosure Advisory ('Do not share')"],
            "indicators_absent": ["Credential Demands", "APK Downloads"],
            "verified_facts": ["Standard bank advisory phrasing identified."],
            "unavailable_context": "Whether the user initiated this transaction is known only to the user.",
            "reason": reason
        }

    # Artificial panic pressure without direct credential demand
    if has_coercive_urgency:
        status = EvidenceStatus.SUSPICIOUS.value
        risk_level = "MEDIUM"
        score = 0.60
        reason = (
            "High artificial urgency or threat detected (e.g., immediate disconnection or account blocking). "
            "Scammers induce urgency to bypass critical thinking." if lang == "en" else
            "अत्यधिक जल्दबाजी या धमकी (जैसे बिजली कटना या खाता बंद होना) की पहचान हुई। "
            "जालसाज सोचने-समझने का मौका न देने के लिए ऐसा कृत्रिम दबाव बनाते हैं।"
        )
        return {
            "pillar_name": "Security & Credential Demands",
            "status": status,
            "status_localized": STATUS_TRANSLATIONS[lang][status],
            "risk_level": risk_level,
            "score": score,
            "indicators_present": ["Coercive Urgency / Penalty Threat"],
            "indicators_absent": ["Direct Credential Demand"],
            "verified_facts": ["Urgent pressure tokens identified."],
            "unavailable_context": "Actual utility or account status requires manual provider verification.",
            "reason": reason
        }

    # Neutral / Benign communication
    status = EvidenceStatus.CONSISTENT.value
    risk_level = "LOW"
    score = 0.15
    reason = (
        "No prohibited credential demands, APK downloads, or coercive threats detected." if lang == "en" else
        "संदेश में कोई पासवर्ड/OTP मांग, APK डाउनलोड या डराने-धमकाने वाले संकेत नहीं मिले हैं।"
    )
    return {
        "pillar_name": "Security & Credential Demands",
        "status": status,
        "status_localized": STATUS_TRANSLATIONS[lang][status],
        "risk_level": risk_level,
        "score": score,
        "indicators_present": [],
        "indicators_absent": ["OTP Demand", "PIN Request", "APK Installation", "Coercive Pressure"],
        "verified_facts": ["Text is free from overt credential solicitation."],
        "unavailable_context": "Private communication channel integrity cannot be established.",
        "reason": reason
    }


def evaluate_context_limits_pillar(user_lang: str = "hi") -> Dict[str, Any]:
    """
    Pillar 4: Context & Verification Limits
    Clearly explains what information is verifiable on-device versus what telecommunication
    telemetry is technically unavailable to end-user applications.
    """
    lang = user_lang if user_lang in STATUS_TRANSLATIONS else "hi"

    verified_capabilities = [
        "Local lexical and syntactic scam pattern matching",
        "Offline TRAI DLT alphanumeric sender header registry check",
        "Lookalike, homoglyph, and typosquatting domain detection",
        "Cryptographically signed offline threat reputation blacklist",
        "Credential solicitation and panic pressure heuristic audit"
    ]

    unavailable_telemetry = [
        "Carrier-level SMPP / SS7 cryptographic packet signatures (Not forwarded to handsets by telecom operators)",
        "Real-time SIM Swap / Porting status (Requires privileged telecom provider HLR/VLR API access)",
        "Cell tower IMSI-catcher or rogue base-station transmission interception telemetry",
        "Live DNS server configuration and SSL/TLS certificate chain validation (100% offline limitation)"
    ]

    if lang == "hi":
        verified_capabilities = [
            "स्थानीय पाठ व सिंटैक्स आधारित ठगी पैटर्न विश्लेषण",
            "ऑफ़लाइन TRAI DLT प्रेषक हेडर डायरेक्ट्री सत्यापन",
            "फर्जी/नकली (लुकअलाइक व टायपोस्कॉटिंग) वेबसाइट डोमेन की पहचान",
            "डिजिटल रूप से हस्ताक्षरित ऑफ़लाइन साइबर फ्रॉड ब्लैकलिस्ट जांच",
            "गोपनीय जानकारी (OTP/पिन) मांगने और डराने वाले संकेतों का ऑडिट"
        ]
        unavailable_telemetry = [
            "टेलीकॉम ऑपरेटर स्तर के SMPP/SS7 क्रिप्टोग्राफिक हस्ताक्षर (हैंडसेट पर उपलब्ध नहीं होते)",
            "वास्तविक समय में सिम स्वैप (SIM Swap) की स्थिति (दूरसंचार कंपनी के आंतरिक सिस्टम से ही संभव)",
            "मोबाइल टावर स्तर पर फर्जी बेस स्टेशन (IMSI-catcher) द्वारा संदेश हेरफेर की जांच",
            "लाइव DNS रिकॉर्ड और वेबसाइट SSL प्रमाणपत्र की तत्काल स्थिति (100% ऑफ़लाइन सीमा)"
        ]
    elif lang == "chg":
        verified_capabilities = [
            "संदेश के लिखावट अउ ठगी के शब्द मन के जांच",
            "ऑफ़लाइन सरकारी TRAI हेडर लिस्ट म मिलान",
            "फर्जी वेबसाइट अउ नकली नाम के पहचान",
            "साइबर सुरक्षा ब्लैकलिस्ट म दर्ज नंबर/लिंक के जांच",
            "OTP या पिन मांगे के चाल के पहचान"
        ]
        unavailable_telemetry = [
            "मोबाइल कंपनी के अंदरूनी क्रिप्टोग्राफिक सिग्नेचर (मोबाइल म नइ मिलय)",
            "सिम बदले (SIM Swap) के लाइव जानकारी (टेलीकॉम कंपनी लगे रहिथे)",
            "टावर स्तर म संदेश के छेड़छाड़ के जांच",
            "इंटरनेट बंद रहे म वेबसाइट के लाइव सर्टिफिकेट जांच"
        ]

    explanation = (
        "Zero-Trust Architecture: Because end-user devices cannot verify carrier-level transmission signatures "
        "or live telecom routing paths, no communication can ever be declared 100% authentic based on appearance alone. "
        "Legitimate formatting merely indicates consistency with known patterns, not cryptographic guarantee." if lang == "en" else
        "जीरो-ट्रस्ट सुरक्षा सिद्धांत: चूंकि उपभोक्ता उपकरण दूरसंचार ऑपरेटर के आंतरिक ट्रांसमिशन हस्ताक्षर की जांच नहीं "
        "कर सकते, इसलिए केवल स्वरूप या हेडर के आधार पर किसी संदेश को 100% प्रामाणिक नहीं माना जा सकता। "
        "सही फॉर्मेट केवल यह दर्शाता है कि संदेश ज्ञात पैटर्न के अनुरूप है, यह पूर्ण सुरक्षा की गारंटी नहीं है।"
    )

    return {
        "pillar_name": "Context & Verification Limits",
        "status": EvidenceStatus.CONSISTENT.value,
        "status_localized": STATUS_TRANSLATIONS[lang][EvidenceStatus.CONSISTENT.value],
        "risk_level": "INFO",
        "score": 0.0,
        "verified_capabilities": verified_capabilities,
        "unavailable_telemetry": unavailable_telemetry,
        "why_it_matters": (
            "Without carrier cryptographic proofs, sender spoofing remains theoretically possible even on standard SMS." if lang == "en" else
            "कैरियर क्रिप्टोग्राफिक प्रमाण के बिना एसएमएस स्पूफिंग की सैद्धांतिक संभावना बनी रहती है।"
        ),
        "zero_trust_statement": explanation
    }


def synthesize_overall_status(
    p1: Dict[str, Any],
    p2: Dict[str, Any],
    p3: Dict[str, Any]
) -> Tuple[str, float]:
    """
    Synthesizes overall evidence status strictly into one of the 4 defined values:
    - Consistent with verified communication patterns
    - Suspicious communication patterns detected
    - Potential impersonation detected
    - Insufficient information to verify

    Calculates an uncalibrated evidence risk index strictly in [0.0, 1.0]
    without claiming absolute probability.
    """
    statuses = [p1["status"], p2["status"], p3["status"]]

    # 1. Impersonation has highest priority
    if EvidenceStatus.POTENTIAL_IMPERSONATION.value in statuses:
        overall = EvidenceStatus.POTENTIAL_IMPERSONATION.value
        risk_index = max(p1["score"], p2["score"], p3["score"])
        return overall, round(min(0.99, max(0.85, risk_index)), 3)

    # 2. Suspicious indicators
    if EvidenceStatus.SUSPICIOUS.value in statuses:
        overall = EvidenceStatus.SUSPICIOUS.value
        risk_index = max(p1["score"], p2["score"], p3["score"])
        return overall, round(min(0.98, max(0.65, risk_index)), 3)

    # 3. Insufficient information
    if EvidenceStatus.INSUFFICIENT_INFO.value in statuses:
        # If any pillar had medium risk score
        if any(p["score"] >= 0.40 for p in [p1, p2, p3]):
            overall = EvidenceStatus.INSUFFICIENT_INFO.value
            return overall, 0.45
        # If all other pillars were consistent
        overall = EvidenceStatus.INSUFFICIENT_INFO.value
        return overall, 0.30

    # 4. Consistent with verified patterns
    overall = EvidenceStatus.CONSISTENT.value
    risk_index = max(p1["score"], p2["score"], p3["score"])
    return overall, round(min(0.20, max(0.05, risk_index)), 3)


def verify_communication(
    text: str,
    sender: Optional[str] = None,
    user_lang: str = "hi"
) -> Dict[str, Any]:
    """
    Main entry point for the Official Communication Verification Engine (OCVE).

    Evaluates 4 independent pillars:
    1. Sender & Channel Authenticity
    2. URL & Domain Integrity
    3. Security & Credential Demands
    4. Context & Verification Limits

    Returns a rich, explainable, zero-trust audit object.
    Never declares any communication 100% genuine or authentic.
    """
    lang = user_lang if user_lang in STATUS_TRANSLATIONS else "hi"

    # Evaluate all 4 pillars independently
    pillar_sender = evaluate_sender_pillar(sender=sender, text=text, user_lang=lang)
    pillar_url = evaluate_url_pillar(text=text, sender=sender, user_lang=lang)
    pillar_security = evaluate_security_demands_pillar(text=text, user_lang=lang)
    pillar_limits = evaluate_context_limits_pillar(user_lang=lang)

    # Synthesize overall evidence status
    overall_status_en, risk_index = synthesize_overall_status(pillar_sender, pillar_url, pillar_security)
    overall_status_localized = STATUS_TRANSLATIONS[lang].get(overall_status_en, overall_status_en)

    # Map status to recommended actions
    rec_key = "consistent"
    if overall_status_en == EvidenceStatus.POTENTIAL_IMPERSONATION.value:
        rec_key = "impersonation"
    elif overall_status_en == EvidenceStatus.SUSPICIOUS.value:
        rec_key = "suspicious"
    elif overall_status_en == EvidenceStatus.INSUFFICIENT_INFO.value:
        rec_key = "insufficient"

    recs = RECOMMENDATIONS.get(lang, RECOMMENDATIONS["hi"]).get(rec_key, [])
    disclaimer = SECURITY_DISCLAIMERS.get(lang, SECURITY_DISCLAIMERS["hi"])

    # Collect all verified facts vs unavailable info
    all_verified_facts = (
        pillar_sender.get("verified_facts", []) +
        pillar_url.get("verified_facts", []) +
        pillar_security.get("verified_facts", [])
    )

    all_unavailable_info = (
        [pillar_sender.get("spoofing_vulnerability")] if pillar_sender.get("spoofing_vulnerability") else []
    ) + (
        [pillar_url.get("unavailable_context")] if pillar_url.get("unavailable_context") else []
    ) + pillar_limits.get("unavailable_telemetry", [])

    return {
        "engine": "Official Communication Verification Engine (OCVE)",
        "version": "1.0.0",
        "overall_status": overall_status_en,
        "overall_status_localized": overall_status_localized,
        "evidence_risk_index": risk_index,
        "is_100_percent_authentic": False,  # Strict invariant: Never claimed true
        "authenticity_claim_prohibited": True,
        "pillars": {
            "sender_authenticity": pillar_sender,
            "url_integrity": pillar_url,
            "security_demands": pillar_security,
            "context_limits": pillar_limits
        },
        "verified_facts": all_verified_facts,
        "unavailable_information": all_unavailable_info,
        "actionable_recommendations": recs,
        "security_disclaimer": disclaimer,
        "language": lang
    }
