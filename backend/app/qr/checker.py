"""
Fake-QR & UPI URI Checker for Suraksha
Decodes QR codes offline with OpenCV QRCodeDetector.
Parses upi:// URI and evaluates payee name vs handle mismatches, collect requests, and lookalike handles.
"""

from urllib.parse import urlparse, parse_qs, unquote
import re
import numpy as np
import cv2
from app.detect.reputation import check_reputation

GOV_OR_BANK_KEYWORDS = [
    "sbi", "state bank", "hdfc", "icici", "cspdcl", "electricity", "bijli",
    "police", "cbi", "customs", "cyber", "income tax", "gst", "pm kisan",
    "treasury", "collector", "panchayat", "rbi", "government"
]

PERSONAL_PSP_HANDLES = [
    "okaxis", "okhdfcbank", "oksbi", "okicici", "paytm", "ybl", "ibl", "axl", "apl"
]

def decode_qr_image_bytes(image_bytes: bytes) -> str:
    """Decodes QR code from image bytes using OpenCV QRCodeDetector."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return ""

    detector = cv2.QRCodeDetector()
    decoded_text, points, _ = detector.detectAndDecode(img)
    return decoded_text or ""

def parse_upi_uri(raw_str: str) -> dict:
    raw_str = raw_str.strip()
    if not raw_str.startswith("upi://"):
        # Check if contains upi:// inside
        match = re.search(r"upi://[^\s\"']+", raw_str)
        if match:
            raw_str = match.group(0)
        else:
            return {
                "valid": False,
                "error": "Not a valid UPI QR URI format (must start with upi://pay)",
                "raw": raw_str
            }

    parsed = urlparse(raw_str)
    params = parse_qs(parsed.query)

    pa = params.get("pa", [""])[0]  # Payee address / UPI ID
    pn = unquote(params.get("pn", [""])[0])  # Payee Name
    am = params.get("am", [""])[0]  # Pre-filled Amount
    cu = params.get("cu", ["INR"])[0]
    tn = unquote(params.get("tn", [""])[0])  # Note
    mode = params.get("mode", [""])[0]

    return {
        "valid": bool(pa),
        "pa": pa,
        "pn": pn,
        "am": am,
        "cu": cu,
        "tn": tn,
        "mode": mode,
        "raw": raw_str
    }

def analyze_upi_qr(raw_qr_str: str, user_lang: str = "hi") -> dict:
    parsed = parse_upi_uri(raw_qr_str)
    if not parsed["valid"]:
        return {
            "verdict": "unsure",
            "confidence_percent": 60,
            "title": "Invalid or Non-UPI QR Code",
            "explanation": "This QR does not appear to be a standard UPI payment QR code.",
            "data": parsed,
            "warnings": ["QR content does not match upi:// URI format."]
        }

    pa = parsed["pa"].lower()
    pn = parsed["pn"].lower()
    am = parsed["am"]
    warnings = []
    risk_score = 0.0

    # Risk Check 0: Check against Ed25519-signed offline reputation blacklist
    rep_match = check_reputation(pa)
    if not rep_match and parsed.get("raw"):
        rep_match = check_reputation(parsed["raw"])
    if rep_match and rep_match.get("is_known_scam"):
        risk_score += 1.0
        warnings.append(
            f"OFFLINE BLACKLIST MATCH: Recipient '{pa}' is listed in the verified cyber defense blacklist ({rep_match.get('scam_type')})."
        )

    # Risk Check 1: Name claims Bank/Gov/Utility but Handle is a personal third-party PSP
    claims_authority = any(kw in pn for kw in GOV_OR_BANK_KEYWORDS)
    handle_provider = pa.split("@")[-1] if "@" in pa else ""
    handle_user = pa.split("@")[0] if "@" in pa else ""

    is_personal_psp = handle_provider in PERSONAL_PSP_HANDLES
    # Check if handle_user looks like a personal name (contains digits or common name patterns)
    has_personal_digits = bool(re.search(r"\d{3,}", handle_user))

    if claims_authority and (is_personal_psp or has_personal_digits):
        risk_score += 0.8
        warnings.append(
            f"CRITICAL MISMATCH: Payee Name claims '{parsed['pn']}' (Bank/Gov/Utility), but the recipient UPI ID '{parsed['pa']}' is a personal account!"
        )

    # Risk Check 2: Lookalike handle pretending to be a bank/utility on a personal PSP
    lookalike_in_user = any(kw in handle_user for kw in ["sbi", "cspdcl", "police", "customs", "kyc", "refund", "lottery"])
    if lookalike_in_user and is_personal_psp:
        risk_score += 0.7
        warnings.append(
            f"LOOKALIKE HANDLE: '{parsed['pa']}' is impersonating an institution using a public payment app."
        )

    # Risk Check 3: Collect Request Disguised as Payment
    if parsed["mode"] in ["02", "collect"] or "collect" in parsed["raw"].lower():
        risk_score += 0.9
        warnings.append(
            "DISGUISED COLLECT REQUEST: This QR will request or pull funds from your account rather than sending money."
        )

    # Risk Check 4: Pre-filled high amount
    if am:
        try:
            amt_val = float(am)
            if amt_val >= 2000:
                risk_score += 0.2
                warnings.append(f"Pre-filled payment amount of ₹{amt_val:.2f} attached.")
        except ValueError:
            pass

    # Verdict assignment
    if risk_score >= 0.7:
        verdict = "likely_scam"
        confidence = 0.95
        title = "Fake QR Code / Impersonation Scam (खतरा)"
        if user_lang == "hi":
            explanation = "सावधान! यह QR कोड किसी संस्था या बैंक का नहीं, बल्कि ठग के निजी खाते का है। पेमेंट करने पर आपके पैसे डूब जाएंगे।"
        elif user_lang == "chg":
            explanation = "सचेत रहव! ये QR कोड कोनो सरकारी दफ्तर के नइये, कोनो ठग लइका के निजी खाता के हे। पइसा कभू झन भेजव।"
        else:
            explanation = "Warning! This QR code attempts impersonation. The payee name does not match the actual recipient account."
    elif risk_score >= 0.3:
        verdict = "unsure"
        confidence = 0.65
        title = "Unsure / Verify Details (जांचें)"
        explanation = "Verify the merchant name with the store owner before proceeding."
    else:
        verdict = "genuine"
        confidence = 0.90
        title = "Looks Genuine (सुरक्षित मर्चेंट)"
        if user_lang == "hi":
            explanation = "क्यूआर विवरण वैध मर्चेंट से मेल खाता है। फिर भी भुगतान करने से पहले प्राप्तकर्ता का नाम अवश्य देखें।"
        elif user_lang == "chg":
            explanation = "QR कोड सही दिखत हे। पइसा भेजे के पहिले दुकानदार के नाव जरूर मिला लव।"
        else:
            explanation = "QR code parameters appear standard. Verify payee name on your UPI app before completing payment."

    return {
        "verdict": verdict,
        "confidence_percent": int(confidence * 100),
        "title": title,
        "explanation": explanation,
        "data": parsed,
        "warnings": warnings,
        "risk_score": round(risk_score, 2)
    }
