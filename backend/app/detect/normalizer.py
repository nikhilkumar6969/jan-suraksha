"""
Text Normalizer and Language Detector for Suraksha
Handles Latin, Devanagari, Chhattisgarhi (CG), and Hinglish phonetic spellings & vocabulary.
"""

import re
import unicodedata

# Hinglish & Chhattisgarhi phonetic normalization dictionary
HINGLISH_AND_CG_MAP = {
    # Hinglish core terms
    r"\botpp?\b": "otp",
    r"\bbijlee?\b": "bijli",
    r"\bbijli\b": "bijli",
    r"\bpulle?s\b": "police",
    r"\bpulis\b": "police",
    r"\bpaise?\b": "paisa",
    r"\bpaaysa\b": "paisa",
    r"\brupy?ee?\b": "rupaye",
    r"\brupees?\b": "rupaye",
    r"\bgirafta+r\b": "arrest",
    r"\barre+st\b": "arrest",
    r"\bcusta?m\b": "customs",
    r"\bpa+rsa?l\b": "parcel",
    r"\btura+nt\b": "immediately",
    r"\bjald[ie]\b": "immediately",
    r"\ba/c\b": "account",
    r"\bacc\b": "account",
    r"\byonoo?\b": "yono",
    r"\banide+sk\b": "anydesk",
    r"\bquiksupport\b": "quicksupport",
    r"\bthana\b": "police station",
    r"\bkat\s+jay?e?ga\b": "disconnected",
    r"\bkat\s+gaya\b": "disconnected",
    r"\bband\s+ho\s+jay?e?ga\b": "blocked",

    # Chhattisgarhi (CG) words & Romanized Chhattisgarhi
    r"\bतोर\b": "तोर",
    r"\bतोला\b": "तोला",
    r"\bपईसा\b": "पैसे",
    r"\bपइसा\b": "पैसे",
    r"\bकट\s*जाही\b": "काट दी जाएगी",
    r"\bकटही\b": "काट दी जाएगी",
    r"\bपटाव\b": "जमा करें",
    r"\bडारव\b": "दर्ज करें",
    r"\bभेजव\b": "भेजें",
    r"\bबताव\b": "बताएं",
    r"\bछुवव\b": "क्लिक करें",
    r"\bझन\b": "मत",
    r"\bनइ\b": "नहीं",
    r"\bहस\b": "हो",
    r"\bहंव\b": "हूँ",
    r"\bसंझा\b": "रात",
    r"\bककरो\b": "किसी",

    # Romanized Chhattisgarhi
    r"\btor\b": "your",
    r"\btola\b": "you",
    r"\bkat\s*jahi\b": "disconnected",
    r"\bpataw\b": "pay",
    r"\bdaraw\b": "enter",
    r"\bbhejaw\b": "send",
    r"\bbataw\b": "tell",
    r"\bjhan\b": "do not",
    r"\bnai\b": "not",
    r"\bsanjha\b": "tonight",
}

# Chhattisgarhi dialect markers (Devanagari & Roman)
CG_MARKERS_DEVA = [
    "तोर", "तोला", "पईसा", "पइसा", "कट जाही", "कटही", "पटाव", "डारव",
    "भेजव", "बताव", "छुवव", "झन", "नइ", "हस", "हंव", "संझा", "ककरो", "महतारी"
]

CG_MARKERS_ROMAN = [
    "tor", "tola", "kat jahi", "katjahi", "pataw", "daraw", "bhejaw",
    "bataw", "jhan", "nai bhare", "sanjha", "mahtari", "howat he"
]

HINGLISH_KEYWORDS = [
    "aapka", "kare", "gaya", "hai", "nahi", "raat", "turant", "paisa",
    "bhaiya", "baje", "karo", "apna", "khata", "bijli", "line", "karna",
    "mat", "paise", "bhejo", "nikla", "bol", "raha", "hoon"
]

def detect_language(text: str) -> str:
    """
    Detects language/dialect:
    - 'chg': Chhattisgarhi (in Devanagari or Roman)
    - 'hi': Standard Hindi (Devanagari)
    - 'hinglish': Hinglish (Hindi in Roman script)
    - 'en': English
    """
    if not text:
        return "en"

    text_lower = text.lower()

    # 1. Check Chhattisgarhi markers
    cg_hits = sum(1 for m in CG_MARKERS_DEVA if m in text)
    cg_roman_hits = sum(1 for m in CG_MARKERS_ROMAN if re.search(r"\b" + m + r"\b", text_lower))
    if cg_hits >= 1 or cg_roman_hits >= 1:
        return "chg"

    # 2. Check Devanagari vs Latin ratio
    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
    total_chars = len(re.findall(r"[a-zA-Z\u0900-\u097F]", text))

    if total_chars == 0:
        return "en"

    ratio = devanagari_chars / total_chars
    if ratio > 0.4:
        return "hi"

    # 3. Check for Hinglish markers in Roman script
    matches = sum(1 for kw in HINGLISH_KEYWORDS if re.search(r"\b" + kw + r"\b", text_lower))
    if matches >= 2:
        return "hinglish"

    return "en"

def normalize_text(text: str) -> dict:
    """
    Normalizes unicode, strips excess whitespace, normalizes Hinglish & CG variants,
    and returns detected script/dialect and clean text.
    """
    if not text:
        return {"original": "", "clean": "", "language": "en", "tokens": []}

    # Normalize unicode (NFC)
    raw = unicodedata.normalize("NFC", text.strip())
    lang = detect_language(raw)

    clean = raw.lower()
    for pattern, repl in HINGLISH_AND_CG_MAP.items():
        clean = re.sub(pattern, repl, clean, flags=re.IGNORECASE)

    # Normalize multiple spaces, tabs, newlines
    clean = re.sub(r"\s+", " ", clean).strip()
    tokens = clean.split()

    return {
        "original": raw,
        "clean": clean,
        "language": lang,
        "tokens": tokens
    }
