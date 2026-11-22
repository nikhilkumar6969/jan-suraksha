"""
Text Normalizer and Language Detector for Suraksha
Handles Latin, Devanagari, Hinglish phonetic spellings, noise stripping.
"""

import re
import unicodedata

# Hinglish phonetic normalization dictionary
HINGLISH_MAP = {
    r"\botpp?\b": "otp",
    r"\bbijlee\b": "bijli",
    r"\bbijli\b": "bijli",
    r"\bpulle?s\b": "police",
    r"\bpulis\b": "police",
    r"\bpaise?\b": "paisa",
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
}

def detect_language(text: str) -> str:
    """Detects if text is primarily Devanagari (Hindi), English, or Hinglish."""
    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
    total_chars = len(re.findall(r"[a-zA-Z\u0900-\u097F]", text))

    if total_chars == 0:
        return "en"

    ratio = devanagari_chars / total_chars
    if ratio > 0.4:
        return "hi"
    
    # Check for Hinglish markers
    hinglish_keywords = ["aapka", "kare", "gaya", "hai", "nahi", "raat", "turant", "paisa", "bhaiya", "baje", "karo"]
    text_lower = text.lower()
    matches = sum(1 for kw in hinglish_keywords if re.search(r"\b" + kw + r"\b", text_lower))
    if matches >= 2:
        return "hinglish"
    
    return "en"

def normalize_text(text: str) -> dict:
    """
    Normalizes unicode, strips excess whitespace, normalizes Hinglish variants,
    and returns detected script and clean text.
    """
    if not text:
        return {"original": "", "clean": "", "language": "en", "tokens": []}

    # Normalize unicode (NFC)
    raw = unicodedata.normalize("NFC", text.strip())
    lang = detect_language(raw)

    clean = raw.lower()
    for pattern, repl in HINGLISH_MAP.items():
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
