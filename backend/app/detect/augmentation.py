"""
Deterministic Adversarial & Dialect Augmentation Module for Suraksha
Generates hardened variants to defend against:
1. Leetspeak & character substitution (@ for a, 0 for o, 1 for i, 3 for e, $ for s)
2. Spaced keywords ('O T P', 'P I N', 'K Y C', 'A n y D e s k')
3. Punctuation insertion ('U.P.I', 'P*I*N', 'Any.Desk')
4. Emoji padding and Unicode obfuscation
5. Cyrillic/Latin homoglyphs ('а', 'е', 'о', 'р')
6. Chhattisgarhi dialect phonetics & Romanized transliterations
"""

import re
import random
from typing import List, Dict, Any

LEET_MAP = {
    'a': '@', 'A': '@',
    'o': '0', 'O': '0',
    'i': '1', 'I': '1',
    'e': '3', 'E': '3',
    's': '$', 'S': '$'
}

HOMOGLYPH_MAP = {
    'a': '\u0430',  # Cyrillic small letter a
    'e': '\u0435',  # Cyrillic small letter ie
    'o': '\u043e',  # Cyrillic small letter o
    'p': '\u0440',  # Cyrillic small letter er
    'c': '\u0441',  # Cyrillic small letter es
    'y': '\u0443',  # Cyrillic small letter u
}

SPACED_KEYWORDS = [
    ("otp", "o t p"),
    ("OTP", "O T P"),
    ("pin", "p i n"),
    ("PIN", "P I N"),
    ("kyc", "k y c"),
    ("KYC", "K Y C"),
    ("upi", "u p i"),
    ("UPI", "U P I"),
    ("anydesk", "any desk"),
    ("AnyDesk", "Any.Desk"),
    ("quicksupport", "quick support"),
    ("QuickSupport", "Quick.Support"),
    ("cspdcl", "c s p d c l"),
    ("CSPDCL", "C S P D C L")
]

EMOJIS = ["⚠️", "🚨", "⚡", "📲", "‼️", "📢"]

def apply_leetspeak(text: str, intensity: float = 0.35) -> str:
    chars = []
    for c in text:
        if c in LEET_MAP and random.random() < intensity:
            chars.append(LEET_MAP[c])
        else:
            chars.append(c)
    return "".join(chars)

def apply_homoglyphs(text: str, intensity: float = 0.35) -> str:
    chars = []
    for c in text:
        if c in HOMOGLYPH_MAP and random.random() < intensity:
            chars.append(HOMOGLYPH_MAP[c])
        else:
            chars.append(c)
    return "".join(chars)

def apply_spaced_keywords(text: str) -> str:
    res = text
    for orig, spaced in SPACED_KEYWORDS:
        res = re.sub(r'\b' + re.escape(orig) + r'\b', spaced, res)
    return res

def apply_emoji_padding(text: str) -> str:
    emoji = random.choice(EMOJIS)
    return f"{emoji} {text} {emoji}"

def apply_chhattisgarhi_dialect_variants(text: str) -> str:
    """Translates common standard terms into Chhattisgarhi phonetic/lexical markers."""
    replacements = [
        (r'\bपैसे\b', 'पईसा'),
        (r'\bरुपये\b', 'रुपिया'),
        (r'\bआपका\b', 'तोर'),
        (r'\bआपको\b', 'तोला'),
        (r'\bजमा करें\b', 'पटाव'),
        (r'\bकट जाएगा\b', 'कट जाही'),
        (r'\bकट जाएगी\b', 'कट जाही'),
        (r'\bमत करना\b', 'झन करव'),
        (r'\bमत बताना\b', 'झन बतावव'),
        (r'\bबताएं\b', 'बताव'),
        (r'\bभेजें\b', 'भेजव'),
        (r'\bशाम\b', 'संझा'),
        (r'\bनहीं\b', 'नइ'),
        (r'\bहोगा\b', 'होही'),
        (r'\bआएगा\b', 'आही')
    ]
    res = text
    for pat, repl in replacements:
        res = re.sub(pat, repl, res)
    return res

def augment_sample(sample: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generates deterministic adversarial/dialect augmented samples for a given training instance.
    """
    augmented = []
    text = sample["text"]
    label = sample["label"]
    lang = sample.get("language", "en")

    # 1. Spaced keywords (e.g. O T P, P I N)
    spaced_text = apply_spaced_keywords(text)
    if spaced_text != text:
        augmented.append({
            "text": spaced_text,
            "label": label,
            "language": lang,
            "augmented": "spaced"
        })

    # 2. Leetspeak
    leet_text = apply_leetspeak(text)
    if leet_text != text:
        augmented.append({
            "text": leet_text,
            "label": label,
            "language": lang,
            "augmented": "leetspeak"
        })

    # 3. For Hindi/Chhattisgarhi samples, generate dialect phonetic variants
    if lang in ("hi", "chg", "hinglish"):
        cg_variant = apply_chhattisgarhi_dialect_variants(text)
        if cg_variant != text:
            augmented.append({
                "text": cg_variant,
                "label": label,
                "language": "chg",
                "augmented": "dialect"
            })

    # 4. Emoji padding
    if label == 1 and random.random() < 0.4:
        augmented.append({
            "text": apply_emoji_padding(text),
            "label": label,
            "language": lang,
            "augmented": "emoji"
        })

    return augmented

def augment_training_dataset(train_samples: List[Dict[str, Any]], seed: int = 42) -> List[Dict[str, Any]]:
    """
    Takes training samples and returns original + augmented samples.
    """
    random.seed(seed)
    augmented_corpus = list(train_samples)
    for sample in train_samples:
        new_variants = augment_sample(sample)
        augmented_corpus.extend(new_variants)
    return augmented_corpus
