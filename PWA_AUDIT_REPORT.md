# 🔍 JAN SURAKSHA — PWA & Full-Stack Deployment Audit Report

**Date:** 2026-11-24  
**Auditor:** Senior PWA & DevOps Security Specialist  
**Application:** Jan Suraksha — Cyber Fraud & Scam Defense Platform  
**Target Environment:** Offline-first PWA (Desktop & Android Chrome), Production Render Cloud Web Service, Standalone Native Android Mirror  

---

## 1. Executive Summary
Jan Suraksha is a mature, offline-first cyber fraud detection and financial literacy platform tailored for first-time digital payment users in rural and semi-urban India (supporting Hindi, English, and Chhattisgarhi). The application features SMS/WhatsApp scam classification, live speech-to-text call analysis with keyword alerts, UPI QR verification, cyber fraud reporting (1930 integration), interactive quizzes, and local analytics.

While the core functionality and heuristic engines are solid and fast, the web layer previously lacked several standard PWA standards, robust service worker caching rules, installation UX prompts, security headers, dynamic port binding, and production-ready ASGI server definitions. This audit catalogs the exact baseline and fixes required.

---

## 2. Architecture Overview

### Frontend
- **Stack:** Plain HTML5, CSS3 with responsive custom properties (`tokens.css`, `app.css`), and modular Vanilla JavaScript (`app.js`, `call.js`, `detector.js`, `qr.js`, `learn.js`, `reports.js`, `dashboard.js`, `i18n.js`, etc.).
- **PWA Assets:** `manifest.json`, `sw.js`, icons in `frontend/assets/icons/`.
- **Multilingual System:** Local JSON dictionary files in `frontend/locales/` (`hi.json`, `en.json`, `chg.json`) loaded locally without network dependency.
- **Client Storage:** `localStorage` for offline report queue (`suraksha_offline_reports`), language choice, theme toggle, and audio preferences.

### Backend
- **Stack:** Python 3.10–3.14 + FastAPI + Starlette + Uvicorn ASGI server.
- **Detection Engine:**
  - Machine Learning: Calibrated Scikit-Learn TF-IDF N-gram model pipeline (`backend/models/scam_model.joblib`).
  - Heuristic Engine: High-precision regex pattern matchers (`rules.py`, `scam_engine.py`) covering UPI fraud, digital arrest, electricity bill scams, lottery, and APK malware lures.
  - TRAI Header Registry: Official government and bank sender ID verification (`trai_header.py`).
  - QR Verification: Local pyzbar / OpenCV UPI parameter verification (`checker.py`).
  - Audio Transcription: Dual-engine local speech pipeline (faster-whisper / Vosk / AudioWorklet PCM WebSocket).
- **Database:** SQLite (`backend/data/suraksha.db`) tracking anonymous community reports, indicators, and cluster summaries.

### Android Native Bridge
- **Stack:** Kotlin 1.9 + Android SDK 34 + AndroidX WebViewAssetLoader.
- **Bridge:** `SurakshaNativeBridge` exposing on-device native vibration, 1930 emergency dialing, foreground CallGuardianService, and offline SMS classification.

---

## 3. Identified Problems & Gap Analysis

### A. PWA Manifest & App Installation Gaps
1. **Maskable Icon Declaration:** `manifest.json` lacked explicit `purpose: "any maskable"` declarations, which Android Chrome requires to prevent ugly white bordering on adaptive icon home screens.
2. **Missing Shortcuts & Categories:** `manifest.json` lacked PWA web app shortcuts (`shortcuts` field) for quick actions (e.g., "Check Scam SMS", "Verify QR", "Live Call Shield") and category metadata (`finance`, `security`, `education`).
3. **Missing Custom BeforeInstallPrompt UI:** `app.js` did not capture `beforeinstallprompt`, leaving users without an in-app "Install Jan Suraksha App" button on mobile browsers.
4. **Offline Fallback Page Missing:** If a user accessed an uncached sub-route without internet, the browser displayed standard dinosaur/connection failure error instead of a branded, reassuring Jan Suraksha offline screen.

### B. Service Worker (`sw.js`) Vulnerabilities & Gaps
1. **Unlisted Core Scripts in Pre-cache:** New scripts like `/js/whisper_stt.js` and `/js/trai_header_ui.js` were missing from `ASSETS_TO_CACHE`, risking incomplete offline execution.
2. **Fake 200 OK on API Fetch Failures:** `sw.js` was returning a fake `Response(JSON.stringify({ status: 'offline' }))` for failed API requests, which masqueraded as HTTP 200 and confused client error-handling code.
3. **Unsafe Cache Put:** The fetch handler called `cache.put(event.request, networkResponse.clone())` indiscriminately without verifying that `event.request.method === 'GET'` or that the response had HTTP 200 status, which causes runtime `TypeError` on POST requests.
4. **Cache Invalidation:** Cache versioning needed automated cleanup to prevent stale asset retention across updates.

### C. Backend Production & Deployment Blockers
1. **Missing Health Check Endpoint:** Neither `/health` nor `/api/health` existed in `main.py`, making cloud orchestrators (Render, Kubernetes, AWS ECS) unable to verify service health.
2. **Hardcoded Host/Port:** When executed directly with `python main.py`, the server defaulted to `127.0.0.1:8000` instead of reading `$PORT` and `$HOST` from the environment.
3. **CORS Specification Violation:** `main.py` configured `allow_origins=["*"]` simultaneously with `allow_credentials=True`. RFC-compliant browsers reject credentials on wildcard origins.
4. **Missing HTTP Security Headers:** Essential defense-in-depth headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`, CSP) were absent.
5. **Database Path Portability:** SQLite DB path was hardcoded to `backend/data/suraksha.db`. An environment variable (`SURAKSHA_DB_PATH`) was needed to support cloud persistent disks.
6. **No `.env.example`:** The repo lacked an `.env.example` documenting all configuration keys (`PORT`, `HOST`, `SURAKSHA_REPORT_SECRET`, `SURAKSHA_DB_PATH`, `WHISPER_MODEL_PATH`).

### D. Mobile UI / Touch Viewport Gaps
1. Mobile viewport meta tag needed `viewport-fit=cover` to support modern Android/iOS notched screens.
2. Certain wide data tables and metric boxes on small screens (320px–360px) had slight horizontal margin overflow risks.
3. Install modal / banner needed touch-friendly dismiss and activation buttons conforming to the 48x48px minimum touch target size.

---

## 4. Remediation Plan

| Phase | Remediation Item | Target File(s) |
|---|---|---|
| **Phase 2** | Upgrade `manifest.json` with maskable icons, shortcuts, description, categories | `frontend/manifest.json` |
| **Phase 3** | Re-engineer `sw.js` with Cache-First for static, Network-First for API with meaningful 503 fallback, safe cache checks, and dedicated `offline.html` | `frontend/sw.js`, `frontend/offline.html` |
| **Phase 4** | Implement custom `beforeinstallprompt` listener, install banner UI, and standalone detection | `frontend/js/app.js`, `frontend/index.html`, `frontend/css/app.css` |
| **Phase 5** | Optimize mobile CSS for safe areas, touch targets, and eliminate horizontal overflow | `frontend/css/app.css` |
| **Phase 6** | Audit client offline fallback, ensure honest UI state, connect queued report sync | `frontend/js/detector.js`, `frontend/js/call.js`, `frontend/js/reports.js` |
| **Phase 7** | Add `/health`, production ASGI `$PORT`/`$HOST` runner, fix CORS, add security headers middleware | `backend/app/main.py` |
| **Phase 8** | Conduct security audit, implement input length bounds, create `.env.example` | `.env.example`, `backend/app/main.py` |
| **Phase 9** | Create `render.yaml` infrastructure-as-code and persistent storage docs | `render.yaml` |
| **Phase 10 & 11** | Run performance checks and automated regression test suite | `PWA_TEST_REPORT.md` |
| **Phase 12, 13 & 14**| Create `DEPLOYMENT_GUIDE.md`, `FINAL_IMPLEMENTATION_REPORT.md`, and package production ZIP | `output/JAN_SURAKSHA_PWA_READY.zip` |
