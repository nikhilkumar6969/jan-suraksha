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

from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

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

@app.on_event("startup")
def startup_event():
    init_db()
    try:
        from app.calls.transcribe import prewarm_models
        prewarm_models()
    except Exception as e:
        logger.warning(f"Speech model prewarm notice: {e}")

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
        # Save temp audio file
        temp_path = backend_dir / "data" / f"temp_{audio.filename}"
        content = await audio.read()
        temp_path.write_bytes(content)
        try:
            target_lang = call_lang or "auto"
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
