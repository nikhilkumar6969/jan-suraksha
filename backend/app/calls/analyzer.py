"""
Scam Call Analyzer for Suraksha
Detects call scripts: Fake Bank KYC, Digital Arrest, Customs/Courier parcel.
Integrates with the unified detection pipeline and provides timeline stage tracking.
"""

from app.detect.pipeline import run_detection_pipeline

CALL_SCRIPTS = {
    "digital_arrest": {
        "title": "Police / CBI Digital Arrest Extortion Call",
        "danger_banner": "🚨 CRITICAL THREAT: The caller is impersonating Law Enforcement to extort money. Hang up immediately!",
        "action_advice": "Do NOT stay on the call. Real police NEVER conduct digital arrests or demand online bond fees. Call 1930 immediately."
    },
    "fake_kyc": {
        "title": "Fake Bank Officer / KYC Suspension Call",
        "danger_banner": "⚠️ SCAM ALERT: Caller is pretending to be a bank official to steal your account credentials.",
        "action_advice": "Never share OTP or install remote-access apps (AnyDesk/QuickSupport). Visit your bank branch directly."
    },
    "customs_courier": {
        "title": "Fake Customs / International Courier Parcel Call",
        "danger_banner": "📦 SCAM ALERT: Caller claims illegal contraband or luxury parcel to demand customs duty.",
        "action_advice": "Do not pay any clearance fees. If you did not ship an international parcel, ignore and report the caller."
    }
}

def analyze_call_transcript(transcript: str, user_lang: str = "hi") -> dict:
    pipeline_res = run_detection_pipeline(transcript, user_lang=user_lang)

    # Detect specific call scripts
    rule_flags = pipeline_res["rule_flags"]
    script_meta = None

    if rule_flags.get("digital_arrest"):
        script_meta = CALL_SCRIPTS["digital_arrest"]
    elif rule_flags.get("fake_kyc"):
        script_meta = CALL_SCRIPTS["fake_kyc"]
    elif "courier" in transcript.lower() or "parcel" in transcript.lower() or "customs" in transcript.lower():
        script_meta = CALL_SCRIPTS["customs_courier"]

    if script_meta and pipeline_res["verdict"] != "likely_scam":
        pipeline_res["verdict"] = "likely_scam"
        pipeline_res["confidence_percent"] = max(pipeline_res["confidence_percent"], 92)

    return {
        **pipeline_res,
        "script_meta": script_meta,
        "transcript": transcript
    }
