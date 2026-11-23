"""
Conversation Memory and 5-Stage Progression Tracker for Real-Time Calls
Maintains rolling in-memory session context (temporary only, zero permanent disk saving).
Tracks 5 distinct attack stages:
1. Trust Establishment
2. Fear & Urgency
3. Sensitive Information Requests
4. Financial Exploitation
5. Device Compromise

Detects claim contradictions / impersonation escalation across conversation timeline.
"""

import re
import time
from typing import Dict, List, Any, Optional

STAGES_CONFIG = {
    1: {
        "key": "trust_establishment",
        "name": "Trust Establishment",
        "name_hi": "भरोसा व पहचान स्थापित करना",
        "name_chg": "पहचान व भरोसा जमाना",
        "description": "Caller introduces themselves with an authoritative persona (Bank, Courier, Police, Customs, Electricity Department, Govt Scheme).",
        "patterns": [
            r"\b(?:sbi|hdfc|icici|pnb|bank\s+manager|customer\s+care|fedex|courier|customs|police|cbi|crime\s+branch|inspector|electricity\s+officer|cspdcl|pm\s+awas|mahtari\s+vandan)\b",
            r"बैंक\s*अधिकारी|कस्टमर\s*केयर|फेडेक्स|कस्टम|पुलिस|थाना|सीबीआई|क्राइम\s*ब्रांच|बिजली\s*अधिकारी|महतारी\s*वंदन|आवास\s*योजना",
            r"थाना\s+ले\s+बोलत\s+हंव|बैंक\s+ले\s+बोलत\s+हंव"
        ],
        "claim_tags": {
            "bank": ["sbi", "hdfc", "icici", "pnb", "bank", "बैंक"],
            "courier_customs": ["fedex", "courier", "customs", "parcel", "कस्टम", "पार्सल"],
            "police_cbi": ["police", "cbi", "crime branch", "inspector", "थाना", "पुलिस", "सीबीआई"],
            "utility": ["electricity", "bijli", "cspdcl", "बिजली"],
            "govt_scheme": ["pm awas", "mahtari vandan", "subsidy", "महतारी"]
        }
    },
    2: {
        "key": "fear_and_urgency",
        "name": "Fear & Urgency",
        "name_hi": "डर व कृत्रिम जल्दबाजी",
        "name_chg": "डरवाना अउ जल्दीबाजी",
        "description": "Caller induces panic with impending arrest, account freeze, power disconnection, or strict deadlines.",
        "patterns": [
            r"\b(?:digital\s+arrest|arrest\s+warrant|fir|narcotics|drugs|account\s+blocked|suspended|power\s+cut|jail|legal\s+action|within\s+10\s+minutes|immediately|aaj\s+raat|turant)\b",
            r"डिजिटल\s*अरेस्ट|वारंट|गिरफ्तार|जेल|खाता\s*बंद|बिजली\s*काट|तुरंत|अभी|आज\s*रात|लाइन\s*कट\s*जाही|झन\s*देरी",
            r"phone\s+mat\s+katna|do\s+not\s+disconnect|stay\s+on\s+call|वीडियो\s*कॉल\s*पर\s*बने\s*रहें"
        ]
    },
    3: {
        "key": "sensitive_info",
        "name": "Sensitive Information Requests",
        "name_hi": "गोपनीय जानकारी की मांग",
        "name_chg": "गुप्त जानकारी मांगना",
        "description": "Solicitation of OTPs, UPI PINs, passwords, ATM CVV, or Aadhaar details.",
        "patterns": [
            r"\b(?:otp|pin|upi\s+pin|cvv|password|verification\s+code|aadhaar\s+card|tell\s+otp|share\s+pin)\b",
            r"ओटीपी|पिन|सीवीवी|पासवर्ड|आधार|ओटीपी\s*बताएं|पिन\s*डालें|डारव|बताव"
        ]
    },
    4: {
        "key": "financial_exploitation",
        "name": "Financial Exploitation",
        "name_hi": "वित्तीय दोहन / जबरन वसूली",
        "name_chg": "पईसा ऐंठना",
        "description": "Demanding monetary transfers, bail bonds, clearance charges, penalty fines, or scanning QR codes.",
        "patterns": [
            r"\b(?:transfer|deposit|send\s+money|bail\s+bond|clearance\s+fee|penalty|fine|scan\s+qr|rs\.?\s*\d+|\d+\s*rupees|paisa\s+bhejo)\b",
            r"रुपये|पैसे|पईसा|जमानत\s*राशि|टैक्स|ट्रांसफर|क्यूआर\s*स्कैन|पईसा\s*पटाव"
        ]
    },
    5: {
        "key": "device_compromise",
        "name": "Device Compromise",
        "name_hi": "डिवाइस हैकिंग / स्क्रीन शेयर",
        "name_chg": "मोबाइल हैक करे के चाल",
        "description": "Instructing victim to install unknown APKs, AnyDesk, TeamViewer, QuickSupport, or grant accessibility access.",
        "patterns": [
            r"\b(?:anydesk|quicksupport|teamviewer|rustdesk|install\s+apk|download\s+apk|screen\s+share|accessibility\s+permission)\b",
            r"एनीडेस्क|क्विक\s*सपोर्ट|टीमव्यूअर|ऐप\s*डाउनलोड|स्क्रीन\s*शेयर|एक्सेसिबिलिटी"
        ]
    }
}

class ConversationTimelineTracker:
    """Tracks state and timeline progression for one active call listening session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.utterances: List[Dict[str, Any]] = []
        self.active_stages: Dict[int, Dict[str, Any]] = {}
        self.observed_claims: List[Dict[str, Any]] = []
        self.claim_contradictions: List[str] = []

    def add_utterance(self, text: str) -> Dict[str, Any]:
        timestamp = time.time()
        text_lower = text.lower()
        self.utterances.append({"text": text, "timestamp": timestamp})

        # 1. Update stages
        newly_triggered = []
        for stage_num, config in STAGES_CONFIG.items():
            matched_words = []
            for pat in config["patterns"]:
                found = re.findall(pat, text_lower, re.IGNORECASE)
                if found:
                    for f in found:
                        word = f if isinstance(f, str) else f[0]
                        if word and word not in matched_words:
                            matched_words.append(word)

            if matched_words:
                if stage_num not in self.active_stages:
                    newly_triggered.append(stage_num)
                    self.active_stages[stage_num] = {
                        "stage_num": stage_num,
                        "key": config["key"],
                        "name": config["name"],
                        "name_hi": config["name_hi"],
                        "name_chg": config["name_chg"],
                        "description": config["description"],
                        "first_seen": timestamp,
                        "matched_words": matched_words
                    }
                else:
                    # Accumulate matches
                    existing = set(self.active_stages[stage_num]["matched_words"])
                    existing.update(matched_words)
                    self.active_stages[stage_num]["matched_words"] = list(existing)

        # 2. Check claim personas in Stage 1
        trust_cfg = STAGES_CONFIG[1]
        for claim_tag, tag_pats in trust_cfg["claim_tags"].items():
            for tp in tag_pats:
                if tp in text_lower:
                    if not any(c["tag"] == claim_tag for c in self.observed_claims):
                        self.observed_claims.append({
                            "tag": claim_tag,
                            "timestamp": timestamp,
                            "evidence": tp
                        })
                    break

        # 3. Detect Claim Inconsistency / Multi-impersonation escalation
        # Example: starts as courier/customs, then introduces police/cbi, then financial extortion
        claim_tags_seen = [c["tag"] for c in self.observed_claims]
        if "courier_customs" in claim_tags_seen and "police_cbi" in claim_tags_seen:
            msg = "Impersonation Escalation: Caller switched from Courier/Customs to Police/CBI."
            if msg not in self.claim_contradictions:
                self.claim_contradictions.append(msg)

        if "bank" in claim_tags_seen and "police_cbi" in claim_tags_seen:
            msg = "Impersonation Escalation: Caller combined Bank Authority claims with Police threats."
            if msg not in self.claim_contradictions:
                self.claim_contradictions.append(msg)

        max_stage = max(self.active_stages.keys()) if self.active_stages else 0
        stage_list = [self.active_stages[s] for s in sorted(self.active_stages.keys())]

        return {
            "current_stage": max_stage,
            "stages_active_count": len(self.active_stages),
            "stages": stage_list,
            "progression_percent": int((len(self.active_stages) / 5.0) * 100),
            "claim_contradictions": self.claim_contradictions,
            "observed_claims": self.observed_claims,
            "newly_triggered": newly_triggered
        }


# Global store for active session trackers
_TRACKERS: Dict[str, ConversationTimelineTracker] = {}


def get_or_create_tracker(session_id: str) -> ConversationTimelineTracker:
    if session_id not in _TRACKERS:
        _TRACKERS[session_id] = ConversationTimelineTracker(session_id)
    return _TRACKERS[session_id]


def track_conversation_step(session_id: str, new_text: str) -> Dict[str, Any]:
    tracker = get_or_create_tracker(session_id)
    return tracker.add_utterance(new_text)


def reset_tracker(session_id: str):
    if session_id in _TRACKERS:
        del _TRACKERS[session_id]
