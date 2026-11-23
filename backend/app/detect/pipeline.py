"""
Unified Fraud Detection Pipeline for Suraksha
Combines Normalizer, ML Classifier, Rule Engine, and Stage Tracker.
Generates highlighted HTML/tokens, plain language explanations in hi/chg/en, and final verdict.
"""

import re
from app.detect.normalizer import normalize_text
from app.detect.rules import check_rules
from app.detect.stage_tracker import track_stages
from app.detect.classifier import classify_text

EXPLANATIONS = {
    "en": {
        "likely_scam_otp": "This message is attempting to steal your OTP or bank security codes. Banks and officers NEVER ask for OTPs.",
        "likely_scam_arrest": "Warning: 'Digital Arrest' is a total extortion scam. Genuine police or CBI never conduct trials or bail demands over phone/video calls.",
        "likely_scam_kyc": "Urgent threats to disconnect power or block bank accounts are fraudulent panic tactics. Never call unknown phone numbers or install APK apps.",
        "likely_scam_generic": "High scam indicators detected. The sender is using artificial urgency or pressure to extract payments or sensitive data.",
        "unsure": "The message contains suspicious keywords or links, but lacks explicit fraud demands. Please cross-verify directly with your bank or official provider.",
        "genuine_bank_otp": "This appears to be a legitimate bank security alert. Notice the explicit safety warning 'DO NOT SHARE WITH ANYONE'. Keep this code secret.",
        "genuine": "No prominent scam patterns detected. However, always stay cautious and never enter your UPI PIN to receive money."
    },
    "hi": {
        "likely_scam_otp": "सावधान! यह संदेश आपका गुप्त OTP या बैंक कोड चुराने की साजिश है। बैंक अधिकारी कभी फोन या मैसेज पर OTP नहीं मांगते।",
        "likely_scam_arrest": "खतरा! 'डिजिटल अरेस्ट' नाम की कोई कानूनी व्यवस्था नहीं है। असली पुलिस या CBI वीडियो कॉल पर पैसे या जमानत की मांग कभी नहीं करती।",
        "likely_scam_kyc": "बिजली काटने या बैंक खाता सील करने की धमकी सरासर फर्जी है। किसी अनजान नंबर पर कॉल न करें और न ही कोई ऐप डाउनलोड करें।",
        "likely_scam_generic": "भारी ठगी का खतरा! प्रेषक आपको डराकर या लालच देकर पैसे या गुप्त जानकारी हथियाने का प्रयास कर रहा है।",
        "unsure": "संदेश संदेहास्पद लग रहा है। किसी भी लिंक पर क्लिक करने से पहले सीधे अपनी बैंक शाखा से पुष्टि कर लें।",
        "genuine_bank_otp": "यह बैंक का वास्तविक सुरक्षा संदेश प्रतीत होता है। इसमें साफ चेतावनी दी गई है कि 'OTP किसी के साथ साझा न करें'। इसे गुप्त रखें।",
        "genuine": "संदेश में कोई ठगी के लक्षण नहीं मिले हैं। फिर भी सतर्क रहें और पैसे पाने के लिए कभी UPI पिन न डालें।"
    },
    "chg": {
        "likely_scam_otp": "सचेत रहव! ये मैसेज तोर गुप्त OTP चुराए के चक्कर हे। बैंक वाले कभू फोन म OTP नइ मांगंय।",
        "likely_scam_arrest": "भारी खतरा! कानून म 'डिजिटल अरेस्ट' नइ होवय। असली पुलिस कभू फोन म पइसा या जमानत नइ मांगय।",
        "likely_scam_kyc": "बिजली काटे या खाता बंद करे के धमकी ठगी आय। कोनो अनजान नंबर म फोन झन लगावव।",
        "likely_scam_generic": "ठगी के भारी खतरा हे! तोर से पइसा ऐंठने बर डरवाए जात हे।",
        "unsure": "संदेश कुछ संदेहास्पद दिखत हे। बैंक जाके एक बेर पूछ लेवव।",
        "genuine_bank_otp": "ए बैंक के सही सुरक्षा संदेश आय। एमा खुद लिखे हे कि 'ककरो ले शेयर झन करव'। अपन OTP संभाल के राखव।",
        "genuine": "संदेश सामान्य दिखत हे। फिर घलो सचेत रहव अउ पइसा पाए बर कभू UPI पिन झन डारव।"
    }
}

def highlight_risky_phrases(original_text: str, risky_phrases: list, safe_phrases: list = None) -> str:
    """Highlights risky phrases in red and safe phrases in green within the original text."""
    if not risky_phrases and not safe_phrases:
        return original_text

    highlighted = original_text
    # Escape and sort by length descending to match longest phrases first
    if safe_phrases:
        for p in sorted(safe_phrases, key=len, reverse=True):
            if len(p.strip()) > 2:
                pattern = re.compile(re.escape(p), re.IGNORECASE)
                highlighted = pattern.sub(f'<span class="highlight-safe">{p}</span>', highlighted)

    for p in sorted(risky_phrases, key=len, reverse=True):
        if len(p.strip()) > 2:
            pattern = re.compile(re.escape(p), re.IGNORECASE)
            highlighted = pattern.sub(f'<span class="highlight-risk">{p}</span>', highlighted)

    return highlighted

def run_detection_pipeline(text: str, user_lang: str = "hi") -> dict:
    if user_lang not in EXPLANATIONS:
        user_lang = "hi"

    # Step 1: Normalization & Language Detection
    norm_res = normalize_text(text)
    clean_text = norm_res["clean"]

    # Step 2: Three Parallel Checks
    # Check 1: ML Classifier
    clf_res = classify_text(clean_text)
    p_scam = clf_res["p_scam"]
    top_ngrams = clf_res["top_contributing_ngrams"]

    # Check 2: Rule Engine (evaluates both normalized and raw text for dialect safety guards)
    rule_res = check_rules(clean_text, raw_text=text)
    rule_flags = rule_res["flags"]
    rule_risk = rule_res["rule_risk_score"]

    # Check 3: Stage Tracker
    stage_res = track_stages(clean_text)

    # Step 3: Combine into Final Verdict
    # Weighting: 0.50 ML Classifier + 0.50 Rule Score
    combined_score = 0.50 * p_scam + 0.50 * rule_risk

    # Rule Overrides:
    # 1. Genuine Alert Override: Bank explicitly warns "do not share OTP" and NO explicit demand
    if rule_flags["is_genuine_alert"] and not rule_flags["explicit_otp_demand"]:
        verdict = "genuine"
        confidence = 0.95
        score = 0.05
        explanation_key = "genuine_bank_otp"
    # 2. Strong Fraud Overrides
    elif rule_flags["explicit_otp_demand"] and rule_flags["urgency_pressure"]:
        verdict = "likely_scam"
        confidence = 0.98
        score = 0.98
        explanation_key = "likely_scam_otp"
    elif rule_flags["digital_arrest"]:
        verdict = "likely_scam"
        confidence = 0.98
        score = 0.98
        explanation_key = "likely_scam_arrest"
    elif rule_flags["fake_kyc"] and (rule_flags["remote_access_apk"] or rule_flags["suspicious_link"] or rule_flags["urgency_pressure"]):
        verdict = "likely_scam"
        confidence = 0.95
        score = 0.95
        explanation_key = "likely_scam_kyc"
    elif combined_score >= 0.55 or p_scam >= 0.70 or rule_risk >= 0.60:
        verdict = "likely_scam"
        confidence = max(p_scam, combined_score)
        score = combined_score
        explanation_key = "likely_scam_generic"
    elif rule_risk >= 0.30 or (combined_score >= 0.38 and len(stage_res["stages"]) > 0):
        verdict = "unsure"
        confidence = combined_score
        score = combined_score
        explanation_key = "unsure"
    else:
        verdict = "genuine"
        confidence = max(0.92, clf_res["p_genuine"])
        score = combined_score
        explanation_key = "genuine"

    # Extract risky & safe phrases for highlighting
    risky_phrases = [m["phrase"] for m in rule_res["matches"] if m.get("risk")]
    safe_phrases = [m["phrase"] for m in rule_res["matches"] if not m.get("risk")]
    
    # Also add words from matched stages
    for s in stage_res["stages"]:
        risky_phrases.extend(s["matched_words"])

    risky_phrases = list(set(risky_phrases))
    safe_phrases = list(set(safe_phrases))

    highlighted_html = highlight_risky_phrases(text, risky_phrases, safe_phrases)

    explanation = EXPLANATIONS[user_lang].get(explanation_key, EXPLANATIONS[user_lang]["likely_scam_generic"])

    return {
        "verdict": verdict,  # "likely_scam" | "unsure" | "genuine"
        "confidence_percent": int(confidence * 100),
        "combined_score": round(score, 3),
        "explanation": explanation,
        "highlighted_html": highlighted_html,
        "risky_phrases": risky_phrases,
        "safe_phrases": safe_phrases,
        "top_ngrams": top_ngrams,
        "stages": stage_res,
        "rule_flags": rule_flags,
        "input_language": norm_res["language"]
    }
