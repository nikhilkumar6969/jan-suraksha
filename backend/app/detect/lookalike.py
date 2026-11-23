"""
Lookalike Domain & Homoglyph Detector for Suraksha
Detects deceptive typosquatting, homoglyph character substitutions, and subdomain traps
targeting official Indian banks, utility providers, and government portals.
Operates 100% offline using deterministic Levenshtein distance and unicode normalization.
"""

import re
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse

# Authoritative registry of official Indian public service & banking domains
OFFICIAL_DOMAINS = {
    "cspdcl": {
        "name": "CSPDCL (Chhattisgarh State Power Distribution)",
        "domains": ["cspdcl.co.in", "cseb.gov.in"],
        "keywords": ["cspdcl", "cseb", "morbijlee", "bijli"]
    },
    "sbi": {
        "name": "State Bank of India (SBI)",
        "domains": ["sbi.co.in", "onlinesbi.sbi", "onlinesbi.com", "bank.sbi"],
        "keywords": ["sbi", "yono", "onlinesbi"]
    },
    "npci": {
        "name": "NPCI / UPI Official",
        "domains": ["npci.org.in", "upi.org.in"],
        "keywords": ["npci", "upi", "bhim"]
    },
    "indiapost": {
        "name": "India Post & IPPB",
        "domains": ["indiapost.gov.in", "ippbonline.com"],
        "keywords": ["indiapost", "ippb", "dakghar"]
    },
    "cybercrime": {
        "name": "National Cybercrime Reporting Portal (I4C)",
        "domains": ["cybercrime.gov.in", "sancharsaathi.gov.in"],
        "keywords": ["cybercrime", "sancharsaathi", "chakshu"]
    },
    "hdfc": {
        "name": "HDFC Bank",
        "domains": ["hdfcbank.com", "hdfc.com"],
        "keywords": ["hdfc", "hdfcbank"]
    },
    "icici": {
        "name": "ICICI Bank",
        "domains": ["icicibank.com"],
        "keywords": ["icici", "icicibank"]
    },
    "pnb": {
        "name": "Punjab National Bank",
        "domains": ["pnbindia.in"],
        "keywords": ["pnb", "pnbindia"]
    },
    "jio": {
        "name": "Reliance Jio",
        "domains": ["jio.com", "myjio.com"],
        "keywords": ["jio", "myjio", "reljio"]
    },
    "airtel": {
        "name": "Bharti Airtel",
        "domains": ["airtel.in", "airtel.com", "airtel.tv"],
        "keywords": ["airtel", "bhartiairtel"]
    },
    "vi": {
        "name": "Vi (Vodafone Idea)",
        "domains": ["myvi.in", "vodafoneidea.com"],
        "keywords": ["vodafone", "myvi"]
    },
    "bsnl": {
        "name": "BSNL",
        "domains": ["bsnl.co.in", "bsnl.in"],
        "keywords": ["bsnl"]
    }
}

# Cyrillic and Greek lookalike character map (true cross-alphabet homoglyphs)
HOMOGLYPH_REPLACEMENTS = {
    '\u0430': 'a', '\u0410': 'A',  # Cyrillic a
    '\u0441': 'c', '\u0421': 'C',  # Cyrillic es / c
    '\u0435': 'e', '\u0415': 'E',  # Cyrillic ie / e
    '\u0456': 'i', '\u0406': 'I',  # Cyrillic Byelorussian-Ukrainian i
    '\u0458': 'j', '\u0408': 'J',  # Cyrillic je
    '\u043e': 'o', '\u041e': 'O',  # Cyrillic o
    '\u0440': 'p', '\u0420': 'P',  # Cyrillic er / p
    '\u0455': 's', '\u0405': 'S',  # Cyrillic dze / s
    '\u0443': 'y', '\u0423': 'Y',  # Cyrillic u / y
    '\u0445': 'x', '\u0425': 'X',  # Cyrillic ha / x
}

# Leetspeak number substitutions for brand matching
LEET_REPLACEMENTS = {
    '0': 'o', '1': 'l', '3': 'e', '5': 's', '@': 'a'
}

def normalize_domain_homoglyphs(domain: str) -> Tuple[str, bool]:
    """Replaces homoglyphs and leet symbols with canonical Latin characters."""
    has_homoglyph = False
    chars = []
    for ch in domain:
        if ch in HOMOGLYPH_REPLACEMENTS:
            chars.append(HOMOGLYPH_REPLACEMENTS[ch])
            has_homoglyph = True
        elif ch in LEET_REPLACEMENTS:
            chars.append(LEET_REPLACEMENTS[ch])
        else:
            chars.append(ch)
    return "".join(chars), has_homoglyph

def extract_urls_and_domains(text: str) -> List[str]:
    """Extracts web links, shortlinks, and bare domains from message text."""
    url_pattern = r'(?:https?:\/\/)?(?:[a-zA-Z0-9_\-\u0400-\u04FF]+\.)+[a-zA-Z]{2,}(?:\/[^\s]*)?'
    raw_matches = re.findall(url_pattern, text)
    extracted = []
    for m in raw_matches:
        # Strip trailing punctuation
        clean_m = re.sub(r'[\.,;!?\)\]>]+$', '', m.strip())
        if clean_m and "." in clean_m:
            extracted.append(clean_m)
    return list(set(extracted))

def get_base_domain(raw_url_or_domain: str) -> str:
    """Extracts lowercased hostname/base domain from a URL or raw string."""
    item = raw_url_or_domain.strip().lower()
    if not item.startswith("http://") and not item.startswith("https://"):
        item = "http://" + item
    parsed = urlparse(item)
    host = parsed.netloc or parsed.path.split("/")[0]
    return host.split(":")[0].strip()

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes standard edit distance between two strings."""
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

def analyze_domain_lookalike(raw_indicator: str) -> Optional[Dict[str, Any]]:
    """
    Checks if a URL or domain is an impersonation / lookalike of a legitimate bank or government domain.
    Returns details if it's deceptive, or None if legitimate/unrelated.
    """
    host = get_base_domain(raw_indicator)
    if not host or "." not in host:
        return None

    norm_host, had_homoglyph = normalize_domain_homoglyphs(host)

    # 1. Exact match against official whitelist
    for target_key, target_info in OFFICIAL_DOMAINS.items():
        for off_dom in target_info["domains"]:
            if host == off_dom or host.endswith("." + off_dom):
                return {
                    "is_official": True,
                    "target": target_info["name"],
                    "domain": host,
                    "risk": False
                }

    # 2. Check for brand keyword presence in unofficial domain
    # e.g. "cspdcl-bill-clear.xyz", "sbi-kyc-update.com", "yono-sbi.net"
    for target_key, target_info in OFFICIAL_DOMAINS.items():
        for kw in target_info["keywords"]:
            # Check if keyword appears in the host name
            if re.search(r'(?:^|[\.-])' + re.escape(kw) + r'(?:[\.-]|$|[a-z0-9])', norm_host):
                # Verify it is not an official domain
                is_official = any(norm_host == od or norm_host.endswith("." + od) for od in target_info["domains"])
                if not is_official:
                    return {
                        "is_lookalike": True,
                        "impersonated_target": target_info["name"],
                        "detected_domain": host,
                        "official_domains": target_info["domains"],
                        "reason": f"Deceptive domain containing official keyword '{kw}', but hosted on an unofficial server.",
                        "reason_hi": f"धोखाधड़ी वाली वेबसाइट: इसमें आधिकारिक संस्था '{target_info['name']}' का नाम उपयोग किया गया है, लेकिन यह फर्जी सर्वर पर है।",
                        "reason_chg": f"फर्जी वेबसाइट: एमा '{target_info['name']}' के फर्जी नाम जोड़ के ठगी करे के चाल चले जात हे।",
                        "had_homoglyphs": had_homoglyph,
                        "risk_level": "HIGH"
                    }

    # 3. Levenshtein edit distance check against official domain names (e.g. cspdcl.com vs cspdcl.co.in)
    host_core = host.split(".")[0]
    for target_key, target_info in OFFICIAL_DOMAINS.items():
        for off_dom in target_info["domains"]:
            off_core = off_dom.split(".")[0]
            dist = levenshtein_distance(host_core, off_core)
            # 1 or 2 character edits away from main entity name
            if 0 < dist <= 2 and len(host_core) >= 4 and len(off_core) >= 4:
                return {
                    "is_lookalike": True,
                    "impersonated_target": target_info["name"],
                    "detected_domain": host,
                    "official_domains": target_info["domains"],
                    "reason": f"Typosquatting domain: '{host}' is deceptively similar to official domain '{off_dom}' (Edit distance: {dist}).",
                    "reason_hi": f"फर्जी वेबसाइट (टायपोस्कॉटिंग): '{host}' असली वेबसाइट '{off_dom}' से मिलती-जुलती बनाकर धोखा देने के लिए बनाई गई है।",
                    "reason_chg": f"फर्जी वेबसाइट: '{host}' असली वेबसाइट ले मिलता-जुलता बना के धोखा देहे बर बनाए गे हे।",
                    "had_homoglyphs": had_homoglyph,
                    "risk_level": "HIGH"
                }

    # 4. Homoglyph with no brand match
    if had_homoglyph and ("." in host):
        return {
            "is_lookalike": True,
            "impersonated_target": "Unknown / Obfuscated Link",
            "detected_domain": host,
            "official_domains": [],
            "reason": f"Domain contains Cyrillic or disguised homoglyph characters: '{host}'.",
            "reason_hi": f"वेबसाइट लिंक में फर्जी छुपे हुए अक्षर (होमोग्लिफ़) पाए गए हैं: '{host}'।",
            "reason_chg": f"वेबसाइट म छुपे हुए फर्जी अक्षर मिले हे: '{host}'।",
            "had_homoglyphs": True,
            "risk_level": "HIGH"
        }

    return None

def detect_lookalikes_in_text(text: str) -> List[Dict[str, Any]]:
    """Scans text for any URLs or domains and returns lookalike evaluations."""
    urls = extract_urls_and_domains(text)
    findings = []
    for u in urls:
        eval_res = analyze_domain_lookalike(u)
        if eval_res and eval_res.get("is_lookalike"):
            findings.append(eval_res)
    return findings
