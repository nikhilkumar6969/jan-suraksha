"""
Suraksha FastAPI Main Application
Offline-first Cyber Fraud Detection & Literacy Platform
"""

import sys
from pathlib import Path
import json

# Ensure backend is in python path
backend_dir = Path(__file__).resolve().parent.parent
workspace_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(workspace_dir) not in sys.path:
    sys.path.insert(0, str(workspace_dir))

from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time
import wave
import logging

logger = logging.getLogger("suraksha.main")

from app.detect.pipeline import run_detection_pipeline
from app.calls.transcribe import transcribe_audio_file
from app.calls.analyzer import analyze_call_transcript
from app.qr.checker import decode_qr_image_bytes, analyze_upi_qr
from app.reports.database import init_db
from app.reports.service import submit_anonymous_report
from app.dashboard.service import get_dashboard_metrics
from app.dashboard.alerts import get_latest_alerts
from app.updates.pack_signer import generate_signed_update_pack, verify_update_pack

app = FastAPI(
    title="Suraksha API",
    description="Offline-First Scam & Cyber Fraud Detection API for Chhattisgarh",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = workspace_dir / "frontend"

MAX_AUDIO_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB max upload
MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB max upload

def cleanup_orphaned_temp_files():
    data_dir = backend_dir / "data"
    if data_dir.exists():
        for f in data_dir.glob("temp_*"):
            try:
                f.unlink(missing_ok=True)
                logger.info(f"Cleaned up orphaned temp file: {f.name}")
            except Exception as e:
                logger.warning(f"Could not clean up temp file {f.name}: {e}")

@app.on_event("startup")
def startup_event():
    init_db()
    cleanup_orphaned_temp_files()
    try:
        from app.calls.transcribe import prewarm_models
        prewarm_models()
    except Exception as e:
        logger.warning(f"Vosk speech model prewarm notice: {e}")
    try:
        from app.calls.streaming_asr import prewarm_all_speech_models
        prewarm_all_speech_models()
    except Exception as e:
        logger.warning(f"Sherpa-ONNX speech model prewarm notice: {e}")

# Models
class MessageCheckRequest(BaseModel):
    text: str
    language: Optional[str] = "hi"

class UpiCheckRequest(BaseModel):
    upi_string: str
    language: Optional[str] = "hi"

class ReportRequest(BaseModel):
    scam_type: str
    district: str
    indicator: str
    device_id: str

# 1. Message Detection Endpoint
@app.post("/api/detect/message")
def detect_message_endpoint(req: MessageCheckRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    result = run_detection_pipeline(req.text, user_lang=req.language or "hi")
    return result

# 2. Call Detection Endpoint (Audio or Transcript)
@app.post("/api/detect/call")
async def detect_call_endpoint(
    audio: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    language: Optional[str] = Form("hi"),
    call_lang: Optional[str] = Form("auto")
):
    final_transcript = ""
    notice = ""

    if audio and audio.filename:
        content = await audio.read()
        if len(content) > MAX_AUDIO_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({len(content) / (1024*1024):.1f} MB). Maximum allowed audio size is 25 MB."
            )
        # Save temp audio file
        temp_path = backend_dir / "data" / f"temp_{audio.filename}"
        temp_path.write_bytes(content)
        try:
            target_lang = call_lang or "auto"
            # Primary: Sherpa-ONNX offline engine (Whisper or Zipformer), with Vosk fallback
            try:
                from app.calls.streaming_asr import offline_transcribe_audio
                trans_res = offline_transcribe_audio(temp_path, lang=target_lang)
            except Exception as ex:
                logger.warning(f"Sherpa-ONNX transcribe fallback: {ex}")
                trans_res = transcribe_audio_file(temp_path, lang=target_lang)

            final_transcript = trans_res.get("text", "")
            notice = trans_res.get("notice", "")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    # Fallback to pasted transcript
    if not final_transcript and transcript:
        final_transcript = transcript.strip()

    if not final_transcript:
        return JSONResponse(
            status_code=200,
            content={
                "verdict": "unsure",
                "confidence_percent": 0,
                "explanation": "No audible voice or text detected. Please paste the call conversation.",
                "notice": notice or "Could not transcribe audio. Please paste call conversation.",
                "stages": {"stages": [], "current_stage": 0, "progression_percent": 0},
                "rule_flags": {},
                "highlighted_html": "",
                "transcript": ""
            }
        )

    analysis = analyze_call_transcript(final_transcript, user_lang=language or "hi")
    if notice:
        analysis["transcription_notice"] = notice
    return analysis

# Real-Time Streaming Audio Chunk Endpoint
@app.post("/api/calls/stream-chunk")
async def stream_chunk_endpoint(
    audio_chunk: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form("default_session"),
    language: Optional[str] = Form("auto"),
    sample_rate: Optional[int] = Form(16000)
):
    from app.calls.streaming_asr import process_streaming_chunk, prepare_16k_mono_wav
    from app.detect.scam_engine import detect_scam_in_transcript
    from app.calls.conversation_tracker import track_conversation_step

    raw_bytes = b""
    if audio_chunk:
        content = await audio_chunk.read()
        if len(content) > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Audio chunk exceeds maximum allowed size of 2 MB."
            )
        # Decode webm/ogg/wav container to 16kHz mono PCM if needed
        fname = audio_chunk.filename or "chunk.wav"
        if any(fname.endswith(ext) for ext in [".webm", ".ogg", ".wav", ".mp3", ".m4a"]):
            temp_in = backend_dir / "data" / f"chunk_in_{session_id}_{fname}"
            temp_out = backend_dir / "data" / f"chunk_out_{session_id}.wav"
            temp_in.write_bytes(content)
            try:
                if prepare_16k_mono_wav(temp_in, temp_out) and temp_out.exists():
                    with wave.open(str(temp_out), "rb") as wf:
                        raw_bytes = wf.readframes(wf.getnframes())
            finally:
                if temp_in.exists():
                    try: temp_in.unlink()
                    except Exception: pass
                if temp_out.exists():
                    try: temp_out.unlink()
                    except Exception: pass
        else:
            raw_bytes = content

    asr_result = process_streaming_chunk(
        session_id=session_id or "default_session",
        pcm_bytes=raw_bytes,
        sample_rate=sample_rate or 16000,
        language=language or "auto"
    )

    current_text = asr_result.get("text", "")
    scam_result = detect_scam_in_transcript(current_text, user_lang=language or "hi")
    timeline_result = track_conversation_step(session_id or "default_session", current_text)

    return {
        **asr_result,
        "scam_assessment": scam_result,
        "timeline": timeline_result,
        "risk_level": scam_result["risk_level"],
        "scam_category": scam_result["scam_category"],
        "reason": scam_result["reason"],
        "recommended_action": scam_result["recommended_action"],
        "audio_warning_hi": scam_result.get("audio_warning_hi", ""),
        "audio_warning_en": scam_result.get("audio_warning_en", ""),
        "audio_warning_chg": scam_result.get("audio_warning_chg", ""),
        "suspicious_phrases": scam_result.get("suspicious_phrases", []),
        "claim_contradictions": timeline_result.get("claim_contradictions", [])
    }

# Session Stop Endpoint
@app.post("/api/calls/session-stop")
def stop_session_endpoint(payload: dict):
    from app.calls.streaming_asr import close_session
    from app.calls.conversation_tracker import reset_tracker
    sid = payload.get("session_id", "default_session")
    sess_summary = close_session(sid)
    reset_tracker(sid)
    return sess_summary or {"status": "stopped", "session_id": sid}

# Full-Duplex Real-Time Streaming WebSocket Endpoint (Direct In-Memory Int16 PCM)
@app.websocket("/api/calls/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    from app.calls.streaming_asr import process_streaming_chunk, close_session
    from app.detect.scam_engine import detect_scam_in_transcript
    from app.calls.conversation_tracker import track_conversation_step, reset_tracker
    import base64

    await websocket.accept()
    session_id = f"ws_{int(time.time()*1000)}"
    current_lang = "auto"
    sample_rate = 16000

    try:
        while True:
            data = await websocket.receive()
            raw_pcm = b""

            if "bytes" in data and data["bytes"]:
                raw_pcm = data["bytes"]
            elif "text" in data and data["text"]:
                try:
                    msg = json.loads(data["text"])
                    msg_type = msg.get("type", "")
                    if msg_type == "config":
                        if msg.get("session_id"):
                            session_id = msg.get("session_id")
                        if msg.get("language"):
                            current_lang = msg.get("language")
                        if msg.get("sample_rate"):
                            sample_rate = int(msg.get("sample_rate"))
                        await websocket.send_json({
                            "status": "ready",
                            "session_id": session_id,
                            "language": current_lang,
                            "sample_rate": sample_rate
                        })
                        continue
                    elif msg_type == "stop":
                        summary = close_session(session_id)
                        reset_tracker(session_id)
                        await websocket.send_json({
                            "status": "stopped",
                            "session_id": session_id,
                            "summary": summary
                        })
                        break
                    if "audio_base64" in msg:
                        raw_pcm = base64.b64decode(msg["audio_base64"])
                    if msg.get("language"):
                        current_lang = msg.get("language")
                except Exception as ex:
                    logger.debug(f"WebSocket JSON decode error: {ex}")

            if raw_pcm and len(raw_pcm) > 0:
                asr_res = process_streaming_chunk(
                    session_id=session_id,
                    pcm_bytes=raw_pcm,
                    sample_rate=sample_rate,
                    language=current_lang
                )
                current_text = asr_res.get("text", "")
                user_lang_pref = current_lang if current_lang in ("hi", "chg", "en") else "hi"
                scam_eval = detect_scam_in_transcript(current_text, user_lang=user_lang_pref)
                timeline_result = track_conversation_step(session_id, current_text)

                payload = {
                    **asr_res,
                    "scam_assessment": scam_eval,
                    "timeline": timeline_result,
                    "stages": timeline_result,
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
                    "audio_warning_chg": scam_eval.get("audio_warning_chg", ""),
                    "suspicious_phrases": scam_eval.get("suspicious_phrases", []),
                    "claim_contradictions": timeline_result.get("claim_contradictions", [])
                }
                await websocket.send_json(payload)
    except WebSocketDisconnect:
        close_session(session_id)
        reset_tracker(session_id)
    except Exception as e:
        logger.error(f"WebSocket streaming error: {e}")
        close_session(session_id)
        reset_tracker(session_id)

# 3. QR Code Analysis Endpoint (Image upload or raw upi:// string)
@app.post("/api/detect/qr")
async def detect_qr_endpoint(
    image: Optional[UploadFile] = File(None),
    upi_string: Optional[str] = Form(None),
    language: Optional[str] = Form("hi")
):
    qr_text = ""
    if image and image.filename:
        content = await image.read()
        if len(content) > MAX_IMAGE_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Image too large ({len(content) / (1024*1024):.1f} MB). Maximum allowed image size is 10 MB."
            )
        qr_text = decode_qr_image_bytes(content)
        if not qr_text:
            return JSONResponse(
                status_code=200,
                content={
                    "verdict": "unsure",
                    "confidence_percent": 50,
                    "title": "No QR Code Found in Image",
                    "explanation": "Could not detect a clear QR pattern in the uploaded photo. Please ensure good lighting or enter the UPI address directly.",
                    "warnings": ["QR code detector found 0 barcodes."],
                    "data": {"valid": False}
                }
            )
    elif upi_string:
        qr_text = upi_string.strip()

    if not qr_text:
        raise HTTPException(status_code=400, detail="Provide either a QR image file or UPI string")

    analysis = analyze_upi_qr(qr_text, user_lang=language or "hi")
    return analysis

# 4. Anonymous Report Submission Endpoint
@app.post("/api/reports/submit")
def submit_report_endpoint(req: ReportRequest):
    result = submit_anonymous_report(
        scam_type=req.scam_type,
        district=req.district,
        raw_indicator=req.indicator,
        raw_device_id=req.device_id
    )
    return result

# 5. Policy Dashboard Metrics Endpoint
@app.get("/api/dashboard/metrics")
def dashboard_metrics_endpoint(district: str = "ALL", time: str = "all"):
    return get_dashboard_metrics(district=district, time_filter=time)

# 6. Emerging Scam Alerts Endpoint
@app.get("/api/dashboard/alerts")
def dashboard_alerts_endpoint():
    return {"alerts": get_latest_alerts()}

# 7. Signed Update Pack Endpoint (Ed25519)
@app.get("/api/updates/pack")
def update_pack_endpoint():
    pack = generate_signed_update_pack()
    return pack

# 8. Evaluation Metrics Endpoint (held-out test split results)
@app.get("/api/evaluation/metrics")
def evaluation_metrics_endpoint():
    metrics_file = backend_dir / "data" / "metrics.json"
    if not metrics_file.exists():
        from app.evaluation.run import run_pipeline
        run_pipeline()
    with open(metrics_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# Serve Frontend static assets
app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")
app.mount("/locales", StaticFiles(directory=str(frontend_dir / "locales")), name="locales")
app.mount("/content", StaticFiles(directory=str(frontend_dir / "content")), name="content")
app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

@app.get("/manifest.json")
def get_manifest():
    return FileResponse(frontend_dir / "manifest.json", media_type="application/manifest+json")

@app.get("/sw.js")
def get_sw():
    return FileResponse(frontend_dir / "sw.js", media_type="application/javascript")

@app.get("/")
def get_index():
    return FileResponse(frontend_dir / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
