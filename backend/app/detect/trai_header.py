"""
Offline TRAI SMS Sender Header Validator & Smishing Defense Engine for Suraksha.
100% On-Device / Offline: Parses DLT operator prefixes, checks brand header registries,
detects 10-digit mobile smishing, catches typosquatting lookalike headers (Levenshtein distance),
and validates domain-header alignment.
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("suraksha.trai_header")

# Configuration weights
DEFAULT_HEADER_WEIGHT = 0.45
DEFAULT_CONTENT_WEIGHT = 0.55

# Shortener domains frequently abused in SMS smishing
KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "is.gd", "cutt.ly", "t.co", "rb.gy",
    "shorturl.at", "ow.ly", "rebrand.ly", "soo.gd", "v.gd"
}

# Suspicious high-risk keywords in body (Hindi, Hinglish, Chhattisgarhi, English)
FINANCIAL_CLAIM_KEYWORDS = [
    # English
    r"\b(?:bank|account|a/c|sbi|hdfc|icici|axis|pnb|bob|kotak|kyc|pan|aadhaar|debit|credit|atm)\b",
    r"\b(?:upi|pin|cashback|refund|subsidy|bonus|lottery|reward|prize|electricity|bill|disconnection|power)\b",
    r"\b(?:income\s*tax|itr|epfo|pf|customs|parcel|arrest|warrant|police|court)\b",
    # Hindi / Hinglish
    r"(?:बैंक|खाता|केवाईसी|आधार|पैन|ओटीपी|पिन|पैसे|रुपये|बिजली|बिल|काट|बंद|फ्रीज|रिफंड|इनाम|लॉटरी|चालान)",
    r"\b(?:paisa|rupaye|bijli|line|kat|pataw|khata|batao|band|inaam)\b",
    # Chhattisgarhi
    r"(?:पईसा|पइसा|तोर|तोला|कट जाही|कटही|पटाव|डारव|भेजव|बताव|झन|संझा|ककरो|महतारी)"
]

URGENCY_KEYWORDS = [
    r"\b(?:urgent|immediately|today|now|24\s*hours?|within\s*\d+\s*(?:mins?|hours?)|expire|blocked|suspended)\b",
    r"(?:तुरंत|अभी|आज\s*रात|बंद\s*हो\s*जाएगा|निलंबित|काट\s*दी\s*जाएगी|काट\s*देबो|अंतिम\s*चेतावनी)",
    r"\b(?:turant|aaj|raat|band|expire|jaldi)\b"
]

APK_DOWNLOAD_KEYWORDS = [
    r"\b[a-zA-Z0-9._-]+\.apk\b",
    r"\.apk\b",
    r"\b(?:download\s+app|install\s+app|support\s+file|quicksupport|anydesk|teamviewer)\b",
    r"(?:ऐप\s*डाउनलोड|एपीके|एप\s*इंस्टॉल|सपोर्ट\s*फाइल)"
]

_HEADERS_CACHE: Optional[Dict[str, Any]] = None


def load_headers_registry() -> Dict[str, Any]:
    """Loads and caches the offline headers.json brand database."""
    global _HEADERS_CACHE
    if _HEADERS_CACHE is not None:
        return _HEADERS_CACHE

    possible_paths = [
        Path(__file__).resolve().parent.parent.parent / "models" / "headers.json",
        Path.cwd() / "backend" / "models" / "headers.json",
        Path.cwd() / "models" / "headers.json",
        Path(__file__).resolve().parent.parent.parent.parent / "android" / "app" / "src" / "main" / "assets" / "headers.json"
    ]

    for p in possible_paths:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                _HEADERS_CACHE = data
                logger.info(f"Loaded TRAI headers registry from {p}")
                return data
            except Exception as e:
                logger.warning(f"Failed to read headers JSON from {p}: {e}")

    logger.warning("headers.json not found in search paths, using built-in minimal registry")
    return {"version": 1, "brands": []}


def parse_sender_id(sender: str) -> Dict[str, Any]:
    """
    Parses a sender string into component parts:
    - Operator prefix (2 letters, e.g. AX, VM, BZ, JZ)
    - Clean 6-character header (e.g. HDFCBK, SBIINB)
    - Suffix (-S, -T, -P, -G)
    - Mobile identification (10-digit / +91)
    """
    if not sender or not isinstance(sender, str):
        return {
            "raw": "",
            "is_mobile": False,
            "mobile_number": None,
            "operator_prefix": None,
            "header": "",
            "suffix": None,
            "is_trai_format": False
        }

    clean = sender.strip()

    # 1. Check for 10-digit or +91 mobile number
    digits_only = re.sub(r"[^\d]", "", clean)
    if digits_only.startswith("91") and len(digits_only) == 12:
        digits_only = digits_only[2:]
    elif digits_only.startswith("0") and len(digits_only) == 11:
        digits_only = digits_only[1:]

    if len(digits_only) == 10 and digits_only[0] in "6789":
        return {
            "raw": clean,
            "is_mobile": True,
            "mobile_number": digits_only,
            "operator_prefix": None,
            "header": digits_only,
            "suffix": None,
            "is_trai_format": False
        }

    # 2. Check standard TRAI format: e.g. AX-HDFCBK, VM-SBIINB-T, BZ-AIRTEL-S
    # Operator Prefix (2 letters) + Hyphen + Header (3-8 letters) + optional Hyphen + Suffix
    trai_match = re.match(r"^([A-Za-z]{2})[-_]([A-Za-z0-9]{3,8})(?:[-_]([STPGstpg]))?$", clean)
    if trai_match:
        prefix = trai_match.group(1).upper()
        header = trai_match.group(2).upper()
        suffix = trai_match.group(3).upper() if trai_match.group(3) else None
        return {
            "raw": clean,
            "is_mobile": False,
            "mobile_number": None,
            "operator_prefix": prefix,
            "header": header,
            "suffix": suffix,
            "is_trai_format": True
        }

    # 3. Clean alphanumeric header without prefix (e.g. "HDFCBK", "SBIINB")
    alpha_clean = re.sub(r"[^A-Za-z0-9]", "", clean).upper()
    return {
        "raw": clean,
        "is_mobile": False,
        "mobile_number": None,
        "operator_prefix": None,
        "header": alpha_clean,
        "suffix": None,
        "is_trai_format": False
    }


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculates Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def extract_domains_from_text(text: str) -> List[Tuple[str, str]]:
    """
    Extracts URLs and their root domain from message text.
    Returns list of (full_url, root_domain).
    """
    url_pattern = re.compile(
        r"(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:/[^\s]*)?",
        re.IGNORECASE
    )
    results = []
    for match in url_pattern.finditer(text):
        full_url = match.group(0)
        domain = match.group(1).lower()
        results.append((full_url, domain))
    return results


def check_sender(sender: str, body: str, user_lang: str = "hi") -> Dict[str, Any]:
    """
    Offline TRAI SMS Header and Smishing analysis.
    Evaluates:
    1. 10-digit mobile number impersonating institutional brands (HIGH/RED)
    2. Header registration match in headers.json
    3. Typosquatting lookalike header detection (distance 1-2)
    4. Header-Brand mismatch (body claims brand X, header is not brand X)
    5. URL domain alignment against brand's registered domains (phishing / shortener check)
    6. Urgency and APK download prompts

    Returns:
    {
        "score": float (0.0 to 1.0, 1.0 = critical risk),
        "level": "RED" | "AMBER" | "GREEN",
        "verdict": "likely_scam" | "unsure" | "genuine",
        "matched_brand": Optional[str],
        "brand_type": Optional[str],
        "reasons": List[Dict[str, str]],
        "header_info": Dict[str, Any],
        "explanation": str
    }
    """
    parsed = parse_sender_id(sender)
    body_clean = body or ""
    registry = load_headers_registry()
    brands = registry.get("brands", [])

    reasons: List[Dict[str, str]] = []
    risk_score = 0.0
    matched_brand: Optional[str] = None
    brand_type: Optional[str] = None
    matched_brand_domains: List[str] = []

    # Check financial / utility claim in body
    has_financial_claim = any(re.search(pat, body_clean, re.IGNORECASE) for pat in FINANCIAL_CLAIM_KEYWORDS)
    has_urgency = any(re.search(pat, body_clean, re.IGNORECASE) for pat in URGENCY_KEYWORDS)
    has_apk = any(re.search(pat, body_clean, re.IGNORECASE) for pat in APK_DOWNLOAD_KEYWORDS)

    # 1. 10-Digit Mobile Number Check
    if parsed["is_mobile"]:
        if has_financial_claim:
            risk_score += 0.85
            reasons.append({
                "rule": "MOBILE_NUMBER_IMPERSONATION",
                "severity": "CRITICAL",
                "en": f"SMS sent from a personal 10-digit mobile number (+91-{parsed['mobile_number']}) while claiming official banking/utility business.",
                "hi": f"यह संदेश व्यक्तिगत 10-अंकों के मोबाइल नंबर (+91-{parsed['mobile_number']}) से आया है जबकि इसमें बैंक/बिजली/सरकारी दावे किए गए हैं। असली बैंक कभी व्यक्तिगत मोबाइल नंबर से संदेश नहीं भेजते।",
                "chg": f"ए संदेश 10 अंक के मोबाइल नंबर (+91-{parsed['mobile_number']}) ले आए हे। असली बैंक कभू साधारण मोबाइल नंबर ले मैसेज नइ भेजंय।"
            })
        else:
            risk_score += 0.30
            reasons.append({
                "rule": "PERSONAL_MOBILE_SENDER",
                "severity": "LOW",
                "en": f"Message received from personal mobile (+91-{parsed['mobile_number']}).",
                "hi": f"व्यक्तिगत मोबाइल नंबर (+91-{parsed['mobile_number']}) से संदेश प्राप्त हुआ।",
                "chg": f"साधारण मोबाइल नंबर (+91-{parsed['mobile_number']}) ले संदेश आए हे।"
            })

    # 2. Check against registered TRAI headers
    header_cand = parsed["header"]
    exact_match = False
    lookalike_found: Optional[Dict[str, Any]] = None

    if header_cand and not parsed["is_mobile"]:
        # Exact match check
        for b in brands:
            if header_cand in [h.upper() for h in b.get("headers", [])]:
                exact_match = True
                matched_brand = b.get("brand")
                brand_type = b.get("type")
                matched_brand_domains = [d.lower() for d in b.get("domains", [])]
                break

        # If not exact match, look for lookalikes (Levenshtein distance 1 or 2)
        if not exact_match and len(header_cand) >= 4:
            for b in brands:
                for reg_h in b.get("headers", []):
                    dist = levenshtein_distance(header_cand, reg_h.upper())
                    if 1 <= dist <= 2:
                        lookalike_found = {
                            "input_header": header_cand,
                            "genuine_header": reg_h.upper(),
                            "brand": b.get("brand"),
                            "distance": dist
                        }
                        break
                if lookalike_found:
                    break

    # Lookalike Header Alert
    if lookalike_found:
        risk_score += 0.90
        reasons.append({
            "rule": "LOOKALIKE_HEADER_TYPOSQUATTING",
            "severity": "CRITICAL",
            "en": f"Header '{lookalike_found['input_header']}' is a deceptive lookalike of genuine registered header '{lookalike_found['genuine_header']}' ({lookalike_found['brand']}).",
            "hi": f"फर्जी हेडर अलर्ट! हेडर '{lookalike_found['input_header']}' असली पंजीकृत हेडर '{lookalike_found['genuine_header']}' ({lookalike_found['brand']}) की नकल (लुक-अलाइव) है।",
            "chg": f"फर्जी हेडर खतरा! हेडर '{lookalike_found['input_header']}' असली हेडर '{lookalike_found['genuine_header']}' के नकल आय।"
        })

    # Header-Brand Mismatch (body mentions brand, but header is completely different)
    if not exact_match and not lookalike_found and not parsed["is_mobile"]:
        for b in brands:
            brand_name = b.get("brand", "").lower()
            short_name = brand_name.split()[0].replace("(", "").replace(")", "")
            if len(short_name) >= 3 and re.search(r"\b" + re.escape(short_name) + r"\b", body_clean, re.IGNORECASE):
                risk_score += 0.65
                reasons.append({
                    "rule": "UNREGISTERED_HEADER_BRAND_MISMATCH",
                    "severity": "HIGH",
                    "en": f"Message body references '{b.get('brand')}', but sender header '{header_cand}' is not an authorized DLT header for this institution.",
                    "hi": f"संदेश में '{b.get('brand')}' का नाम लिखा है, परंतु भेजने वाला हेडर '{header_cand}' इस बैंक/संस्था का अधिकृत DLT हेडर नहीं है।",
                    "chg": f"संदेश म '{b.get('brand')}' के नाम हे, फेर हेडर '{header_cand}' ए संस्था के रजिस्टर्ड हेडर नइ आय।"
                })
                break

    # 3. URL / Domain Verification
    extracted_urls = extract_domains_from_text(body_clean)
    has_shortener = False
    domain_mismatch = False

    for url_str, domain in extracted_urls:
        # Check shortener
        if any(domain.endswith(s) for s in KNOWN_SHORTENERS):
            has_shortener = True
            risk_score += 0.40
            reasons.append({
                "rule": "URL_SHORTENER_DETECTED",
                "severity": "HIGH",
                "en": f"Concealed destination detected via link shortener ({domain}). Legitimate banking OTPs do not use public link shorteners.",
                "hi": f"संदेश में छुपा हुआ शॉर्ट लिंक ({domain}) मिला है। असली बैंक महत्वपूर्ण सूचनाओं के लिए पब्लिक शॉर्टलिंक का उपयोग नहीं करते।",
                "chg": f"मैसेज म लुकाए होए शॉर्ट लिंक ({domain}) हे। बैंक कभू शॉर्ट लिंक नइ भेजंय।"
            })

        # If brand was matched, verify domain alignment
        if exact_match and matched_brand_domains:
            is_valid_domain = any(domain == bd or domain.endswith("." + bd) for bd in matched_brand_domains)
            if not is_valid_domain and not has_shortener:
                domain_mismatch = True
                risk_score += 0.85
                reasons.append({
                    "rule": "BRAND_DOMAIN_MISMATCH",
                    "severity": "CRITICAL",
                    "en": f"Phishing Risk: Sender claims to be {matched_brand}, but the enclosed link points to an unauthorized domain ({domain}) instead of official {matched_brand_domains[0]}.",
                    "hi": f"फ़िशिंग लिंक का खतरा! प्रेषक {matched_brand} का अधिकृत हेडर है, परंतु संदेश में दिया गया लिंक किसी बाहरी वेबसाइट ({domain}) पर ले जा रहा है। असली वेबसाइट: {matched_brand_domains[0]}।",
                    "chg": f"फर्जी लिंक खतरा! हेडर {matched_brand} दिखत हे, फेर लिंक बाहरी साइट ({domain}) के हे।"
                })

    # 4. Urgency & APK Penalties
    if has_urgency:
        risk_score += 0.15
        reasons.append({
            "rule": "ARTIFICIAL_URGENCY",
            "severity": "MEDIUM",
            "en": "Artificial urgency cues detected (threats of immediate account block or line disconnection).",
            "hi": "घबराहट पैदा करने वाले शब्द पहचाने गए (तुरंत खाता बंद होने या बिजली कटने की धमकी)।",
            "chg": "डरवाए बर तुरंत खाता बंद करे या बिजली काटे के धमकी देहे जात हे।"
        })

    if has_apk:
        risk_score += 0.60
        reasons.append({
            "rule": "MALICIOUS_APK_DOWNLOAD",
            "severity": "CRITICAL",
            "en": "Malicious App / APK download detected. Official banks and government bodies NEVER distribute APK files via SMS.",
            "hi": "संदेश में अज्ञात मोबाइल ऐप या APK फ़ाइल डाउनलोड करने को कहा गया है। बैंक कभी एसएमएस पर APK नहीं भेजते।",
            "chg": "एसएमएस म ऐप या APK डाउनलोड करे बर कहे जात हे। बैंक कभू एपीके नइ भेजंय।"
        })

    # 5. Genuine Clean Pattern Bonus
    # If exact registered header + no links + genuine OTP warning words -> safe
    if exact_match and not extracted_urls and not has_apk and not has_urgency and not lookalike_found:
        is_clean_otp = bool(re.search(r"\b(?:otp|code|verification|do not share|kisi ko na bataye|साझा न करें)\b", body_clean, re.IGNORECASE))
        if is_clean_otp:
            risk_score = max(0.0, risk_score - 0.40)
            reasons.append({
                "rule": "GENUINE_REGISTERED_HEADER",
                "severity": "SAFE",
                "en": f"Official registered TRAI DLT header verified for {matched_brand}. Message contains normal security warning with no links.",
                "hi": f"प्रमाणित हेडर: यह {matched_brand} का पंजीकृत सरकारी DLT हेडर है। संदेश में कोई संदेहास्पद लिंक नहीं है।",
                "chg": f"प्रमाणित हेडर: ए {matched_brand} के असली रजिस्टर्ड हेडर आय। कोनो लिंक नइ हे।"
            })

    # Normalize risk score between 0.0 and 1.0
    risk_score = round(min(1.0, max(0.0, risk_score)), 2)

    # Determine risk level
    if risk_score >= 0.70:
        level = "RED"
        verdict = "likely_scam"
    elif risk_score >= 0.35:
        level = "AMBER"
        verdict = "unsure"
    else:
        level = "GREEN"
        verdict = "genuine"

    # Select concise 1-line localized explanation
    lang_key = user_lang if user_lang in ("hi", "chg", "en") else "hi"
    explanation = _generate_one_line_summary(level, reasons, lang_key, matched_brand, parsed)

    return {
        "score": risk_score,
        "level": level,
        "verdict": verdict,
        "matched_brand": matched_brand,
        "brand_type": brand_type,
        "reasons": reasons,
        "header_info": parsed,
        "explanation": explanation
    }


def _generate_one_line_summary(
    level: str,
    reasons: List[Dict[str, str]],
    lang: str,
    brand: Optional[str],
    parsed: Dict[str, Any]
) -> str:
    """Generates a concise 1-line verdict summary for notifications and UI badges."""
    # Priority 1: Top critical reason
    for r in reasons:
        if r.get("severity") == "CRITICAL" and lang in r:
            return r[lang]

    # Priority 2: High reason
    for r in reasons:
        if r.get("severity") == "HIGH" and lang in r:
            return r[lang]

    # Defaults by level
    if level == "RED":
        if lang == "chg":
            return "भारी खतरा! फर्जी हेडर या साधारण मोबाइल नंबर ले ठगी के संदेश आय।"
        elif lang == "en":
            return "Critical Risk: Suspicious or fraudulent SMS header detected."
        return "भारी खतरा! फर्जी हेडर या व्यक्तिगत मोबाइल नंबर से ठगी का प्रयास।"

    elif level == "AMBER":
        if lang == "chg":
            return "सचेत रहव! संदेश म संदेहास्पद लिंक या हेडर के गड़बड़ी दिखत हे।"
        elif lang == "en":
            return "Caution: Unverified sender or suspicious urgency cues detected."
        return "सावधान! अपंजीकृत हेडर या संदेहास्पद लिंक पहचाना गया।"

    else:
        brand_name = brand or parsed.get("header") or "Official Provider"
        if lang == "chg":
            return f"सुरक्षित संदेश: {brand_name} के अधिकृत हेडर ले सत्यापित आय।"
        elif lang == "en":
            return f"Verified Sender: Authentic message from {brand_name}."
        return f"सुरक्षित संदेश: {brand_name} के अधिकृत हेडर से सत्यापित।"


def combine_header_and_content_verdict(
    header_res: Dict[str, Any],
    content_res: Dict[str, Any],
    header_weight: float = DEFAULT_HEADER_WEIGHT,
    content_weight: float = DEFAULT_CONTENT_WEIGHT
) -> Dict[str, Any]:
    """
    Combines the TRAI Header check score with the ML content classification score.
    Dynamically escalates to RED if either critical lookalike or 10-digit financial impersonation is present.
    """
    h_score = header_res.get("score", 0.0)
    c_score = content_res.get("probability_score", 0.0)

    # If header found a critical flaw (lookalike or personal mobile claiming bank), ensure minimum score
    has_critical_header = any(r.get("severity") == "CRITICAL" for r in header_res.get("reasons", []))
    if has_critical_header:
        fused_score = max(0.85, (h_score * 0.60) + (c_score * 0.40))
    else:
        fused_score = (h_score * header_weight) + (c_score * content_weight)

    fused_score = round(min(1.0, max(0.0, fused_score)), 2)

    if fused_score >= 0.70:
        final_level = "RED"
        final_verdict = "likely_scam"
    elif fused_score >= 0.35:
        final_level = "AMBER"
        final_verdict = "unsure"
    else:
        final_level = "GREEN"
        final_verdict = "genuine"

    return {
        "fused_score": fused_score,
        "level": final_level,
        "verdict": final_verdict,
        "header_analysis": header_res,
        "content_analysis": content_res
    }
