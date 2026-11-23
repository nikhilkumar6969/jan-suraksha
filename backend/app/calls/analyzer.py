"""
Scam Call Analyzer for Suraksha
Integrates real-time scam engine, conversation stage tracking, and unified pipeline.
Supports multi-lingual localized script metadata in Hindi, Chhattisgarhi, and English.
"""

from typing import Dict, Any, Optional
from app.detect.pipeline import run_detection_pipeline
from app.detect.scam_engine import detect_scam_in_transcript
from app.calls.conversation_tracker import track_conversation_step, reset_tracker

CALL_SCRIPTS = {
    "digital_arrest": {
        "hi": {
            "title": "पुलिस / सीबीआई डिजिटल अरेस्ट जबरन वसूली",
            "danger_banner": "🚨 गंभीर खतरा: कॉलर पुलिस/सीबीआई बनकर गिरफ्तारी का डर दिखाकर पैसे ऐंठने का प्रयास कर रहा है। तुरंत फोन काटें!",
            "action_advice": "कॉल पर बिल्कुल न रहें। असली पुलिस कभी 'डिजिटल अरेस्ट' नहीं करती और न ही ऑनलाइन जमानत राशि मांगती है। 1930 डायल करें।"
        },
        "chg": {
            "title": "पुलिस / सीबीआई डिजिटल अरेस्ट पईसा ऐंठे के कॉल",
            "danger_banner": "🚨 भारी खतरा: फोन करने वाला पुलिस बनके डरावा देत हे अउ पईसा मांगत हे। तुरते फोन ल काटव!",
            "action_advice": "फोन म झन रहव। कानून म 'डिजिटल अरेस्ट' नइ होवय। असली पुलिस कभू फोन म जमानत नइ मांगय। तुरते 1930 म फोन लगावव।"
        },
        "en": {
            "title": "Police / CBI Digital Arrest Extortion Call",
            "danger_banner": "🚨 CRITICAL THREAT: The caller is impersonating Law Enforcement to extort money. Hang up immediately!",
            "action_advice": "Do NOT stay on the call. Real police NEVER conduct digital arrests or demand online bond fees. Call 1930 immediately."
        }
    },
    "fake_kyc": {
        "hi": {
            "title": "फर्जी बैंक अधिकारी / खाता व बिजली बंद की धमकी",
            "danger_banner": "⚠️ ठगी का अलर्ट: कॉलर बैंक अधिकारी बनकर आपका खाता या डेबिट कार्ड बंद करने की धमकी दे रहा है।",
            "action_advice": "किसी को भी अपना OTP न बताएं और न ही AnyDesk या QuickSupport ऐप डाउनलोड करें। सीधे अपनी बैंक शाखा जाएं।"
        },
        "chg": {
            "title": "फर्जी बैंक अधिकारी / खाता अउ बिजली बंद करे के धमकी",
            "danger_banner": "⚠️ ठगी के अलर्ट: तोर खाता या बिजली काटे के डर दिखा के ठगे के कोसिस हे।",
            "action_advice": "ककरो ले अपन OTP झन बतावव अउ कोनो अनजान ऐप डाउनलोड झन करव। सीधा अपन बैंक शाखा जाके पूछव।"
        },
        "en": {
            "title": "Fake Bank Officer / KYC Suspension Call",
            "danger_banner": "⚠️ SCAM ALERT: Caller is pretending to be a bank official to steal your account credentials.",
            "action_advice": "Never share OTP or install remote-access apps (AnyDesk/QuickSupport). Visit your bank branch directly."
        }
    },
    "customs_courier": {
        "hi": {
            "title": "फर्जी कस्टम्स / पार्सल ड्रग्स घोटाला",
            "danger_banner": "📦 ठगी का अलर्ट: कॉलर आपके नाम पर अवैध पार्सल मिलने का दावा कर कस्टम शुल्क मांग रहा है।",
            "action_advice": "किसी भी तरह का टैक्स या क्लीयरेंस शुल्क न दें। यदि आपने विदेश से पार्सल नहीं भेजा है तो कॉलर को ब्लॉक करें।"
        },
        "chg": {
            "title": "फर्जी कस्टम्स / पार्सल म ड्रग्स के धोखा",
            "danger_banner": "📦 ठगी के अलर्ट: तोर पार्सल म नशीली दवा मिले के झूठा दावा करके पईसा मांगे जात हे।",
            "action_advice": "कोनो टैक्स या क्लीयरेंस फीस झन देहू। कॉलर ल सीधा ब्लॉक करव अउ 1930 म रिपोर्ट करव।"
        },
        "en": {
            "title": "Fake Customs / International Courier Parcel Call",
            "danger_banner": "📦 SCAM ALERT: Caller claims illegal contraband or luxury parcel to demand customs duty.",
            "action_advice": "Do not pay any clearance fees. If you did not ship an international parcel, ignore and report the caller."
        }
    },
    "upi_pin_fraud": {
        "hi": {
            "title": "UPI PIN चोरी का अत्यंत गंभीर खतरा",
            "danger_banner": "🛑 अत्यंत गंभीर खतरा: कॉलर कैशबैक या रिफंड का झांसा देकर आपका गुप्त UPI PIN चुराने का प्रयास कर रहा है।",
            "action_advice": "याद रखें, पैसे प्राप्त करने के लिए कभी UPI PIN दर्ज नहीं करना पड़ता। कॉल तुरंत काटें और 1930 पर शिकायत करें।"
        },
        "chg": {
            "title": "UPI पिन चुराए के भारी खतरा",
            "danger_banner": "🛑 भारी खतरा: कॉलर पईसा मिले के लालच देके तोर गुप्त UPI पिन मांगे के चाल चलत हे।",
            "action_advice": "सचेत रहव! पईसा पाए बर कभू UPI पिन नइ डारे लगत। कॉल तुरते काटव अउ 1930 म शिकायत करव।"
        },
        "en": {
            "title": "Urgent UPI PIN Theft Fraud",
            "danger_banner": "🛑 CRITICAL HAZARD: Caller is trying to steal your UPI PIN under pretext of cashback/refund.",
            "action_advice": "Never enter or tell your UPI PIN to receive money. Disconnect immediately and call 1930."
        }
    }
}


def analyze_call_transcript(
    transcript: str,
    user_lang: str = "hi",
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes call transcript using contextual scam detection,
    5-stage timeline tracker, and pipeline classifier.
    Localized in user_lang ('hi', 'chg', or 'en').
    """
    sid = session_id or "static_call_analysis"
    lang_key = user_lang if user_lang in ("hi", "chg", "en") else "hi"

    # 1. Real-time Scam Engine
    scam_eval = detect_scam_in_transcript(transcript, user_lang=lang_key)

    # 2. 5-Stage Conversation Timeline
    stage_eval = track_conversation_step(sid, transcript)

    # 3. Base Pipeline for classification & highlights
    pipeline_res = run_detection_pipeline(transcript, user_lang=lang_key)

    # Script metadata mapping with multi-lingual localization
    script_meta = None
    script_key = None
    if scam_eval["risk_level"] == "CRITICAL" and "upi_pin_fraud" in scam_eval.get("matched_categories", []):
        script_key = "upi_pin_fraud"
    elif "police_govt_impersonation" in scam_eval.get("matched_categories", []) or "digital_arrest" in transcript.lower():
        script_key = "digital_arrest"
    elif "bank_impersonation" in scam_eval.get("matched_categories", []) or "fake_kyc" in transcript.lower():
        script_key = "fake_kyc"
    elif any(x in transcript.lower() for x in ["courier", "parcel", "customs", "पार्सल"]):
        script_key = "customs_courier"

    if script_key and script_key in CALL_SCRIPTS:
        meta_dict = CALL_SCRIPTS[script_key]
        script_meta = meta_dict.get(lang_key, meta_dict.get("hi", meta_dict.get("en")))

    # Merge verdict and confidence
    if scam_eval["risk_level"] in ("HIGH", "CRITICAL"):
        pipeline_res["verdict"] = "likely_scam"
        pipeline_res["confidence_percent"] = max(pipeline_res.get("confidence_percent", 0), int(scam_eval["confidence"] * 100))
        pipeline_res["explanation"] = scam_eval["reason"]
    elif scam_eval["risk_level"] == "LOW" and not scam_eval["is_scam"]:
        if pipeline_res.get("verdict") == "likely_scam" and not any(k in transcript.lower() for k in ["otp", "pin", "arrest", "warrant", "anydesk"]):
            pipeline_res["verdict"] = "genuine"
            pipeline_res["confidence_percent"] = 95
            pipeline_res["explanation"] = scam_eval["reason"]

    return {
        **pipeline_res,
        "script_meta": script_meta,
        "script_meta_map": CALL_SCRIPTS.get(script_key) if script_key else None,
        "transcript": transcript,
        "risk_level": scam_eval["risk_level"],
        "scam_category": scam_eval["scam_category"],
        "scam_category_hi": scam_eval.get("scam_category_hi", scam_eval["scam_category"]),
        "scam_category_en": scam_eval.get("scam_category_en", scam_eval["scam_category"]),
        "scam_category_chg": scam_eval.get("scam_category_chg", scam_eval["scam_category"]),
        "reason": scam_eval["reason"],
        "reason_hi": scam_eval.get("reason_hi", scam_eval["reason"]),
        "reason_en": scam_eval.get("reason_en", scam_eval["reason"]),
        "reason_chg": scam_eval.get("reason_chg", scam_eval["reason"]),
        "recommended_action": scam_eval["recommended_action"],
        "recommended_action_hi": scam_eval.get("recommended_action_hi", scam_eval["recommended_action"]),
        "recommended_action_en": scam_eval.get("recommended_action_en", scam_eval["recommended_action"]),
        "recommended_action_chg": scam_eval.get("recommended_action_chg", scam_eval["recommended_action"]),
        "audio_warning_hi": scam_eval.get("audio_warning_hi", ""),
        "audio_warning_en": scam_eval.get("audio_warning_en", ""),
        "suspicious_phrases": scam_eval.get("suspicious_phrases", []),
        "matched_categories": scam_eval.get("matched_categories", []),
        "stages": stage_eval,
        "claim_contradictions": stage_eval.get("claim_contradictions", [])
    }
