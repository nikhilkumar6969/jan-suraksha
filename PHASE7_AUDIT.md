# Jan Suraksha — Phase 7 Technical Audit & Release Readiness Report

**Document ID:** `PHASE7_AUDIT.md`  
**Date:** November 23, 2026  
**Auditor:** Jan Suraksha AI Systems Engineering Team  
**Scope:** Real-Time Offline AI Scam Call Guardian, Android Architecture, Dialect Robustness, Privacy & Security

---

## 1. System Component Audits

### 1.1 FastAPI Backend & WebSocket Streaming
* **Current State:**
  - Full-duplex WebSocket endpoint at `/api/calls/stream` ingesting raw 16 kHz Int16 PCM frames (128ms / 2048 samples) directly in RAM.
  - Zero disk I/O in the primary streaming path.
  - Latency measured at `< 150ms` end-to-end.
  - Clean `config`, `chunk`, `stop`, and `ping` control message handling.
* **Identified Gaps & Deficiencies:**
  - **Missing Payload Key:** In `backend/app/main.py` lines 303-304, the WebSocket emission forwards `audio_warning_hi` and `audio_warning_en`, but omits `audio_warning_chg`. If a client requests Chhattisgarhi alerts, the specific dialect text is absent from the payload.
  - **Unbounded HTTP Fallback Uploads:** In `/api/detect/call` and `/api/calls/stream-chunk`, `await audio.read()` lacks explicit payload size limits, leaving the server vulnerable to memory exhaustion from multi-hundred-megabyte payloads.
  - **Orphaned Temp Files Risk:** The fallback HTTP endpoints write temporary files (`temp_*`, `chunk_in_*`) and delete them in `finally` blocks, but unexpected process terminations could leave residual files in `backend/data/`.

---

### 1.2 Sherpa-ONNX & Silero VAD Integration
* **Current State:**
  - Silero VAD v4 windowing (512 samples / 32ms frames) filters background noise and non-speech segments.
  - Sherpa-ONNX streaming Zipformer (`accept_waveform`, `is_ready`, `decode_stream`) performs continuous on-device transcription.
  - Automatic fallback cascade to Whisper Tiny INT8 and Vosk 0.3.45.
* **Identified Gaps & Deficiencies:**
  - **Acoustic Reality for Chhattisgarhi:** No public pre-trained streaming Zipformer exists natively for Chhattisgarhi. The system depends on Hindi/multilingual acoustic models coupled with dialect-level phonological mapping.
  - **VAD Threshold Under High Noise:** In loud rural ambient environments (tractors, street noise, bazaar crowds), a static 20% speech-window threshold can occasionally misclassify ambient noise as speech or clip soft speakers.

---

### 1.3 Hindi, Hinglish & Chhattisgarhi Scam Detection
* **Current State:**
  - Contextual intent recognition across 6 fraud types: UPI PIN fraud, OTP theft, Bank impersonation/KYC threats, Police/Digital arrest, Financial extortion, and Remote access/APK fraud.
  - Progress tracking via 5-stage conversation lifecycle (`ConversationTimelineTracker`).
  - False-positive suppression for bank notifications and user narration.
  - 100% precision and recall achieved on the initial 20-scenario benchmark dataset.
* **Identified Gaps & Deficiencies:**
  - **Missing Chhattisgarhi Audio Warning Text in Engine:** `backend/app/detect/scam_engine.py` generates `audio_warning_hi` and `audio_warning_en`, but does not set `audio_warning_chg` in its return dictionary.
  - **Dataset Representativeness:** The 20-scenario dataset is a curated benchmark, but does not capture the full diversity of rural phonetics, low-volume speakers, heavy background distortion, and multi-speaker overlapping dialogues across all 5 key administrative divisions of Chhattisgarh (Bastar, Surguja, Raipur, Bilaspur, Durg).

---

### 1.4 Offline Audio Alerts & Service Worker Caching
* **Current State:**
  - Complete library of 18 pre-synthesized studio-grade 16-bit PCM WAV alert files plus 1 harmonic attention chime (`alert_chime.wav`).
  - Service Worker v2.0 (`frontend/sw.js`) pre-caches all alert files, JavaScript processors, and stylesheets.
  - Cascading fallback in `frontend/js/call.js`: plays local audio files with 0ms inference overhead; defaults to Web Speech API only as secondary fallback.
* **Identified Gaps & Deficiencies:**
  - **Mobile Browser Autoplay Restrictions:** Mobile browsers require an initial user gesture before allowing audio playback. While the user clicks "Start Listening" or "Test TTS", unhandled autoplay rejections must always smoothly fall back without interrupting streaming.

---

### 1.5 Capacitor Configuration & Android Native Architecture
* **Current State:**
  - `capacitor.config.json` configured for `org.suraksha.sms` targeting `frontend/`.
  - `AndroidManifest.xml` configured with `RECORD_AUDIO`, `MODIFY_AUDIO_SETTINGS`, `VIBRATE`, `FOREGROUND_SERVICE`, and `FOREGROUND_SERVICE_MICROPHONE`.
  - Speakerphone advisory banner live in the UI across Hindi, Chhattisgarhi, and English.
* **Identified Gaps & Deficiencies:**
  - **Missing Service Class:** `AndroidManifest.xml` declares `<service android:name=".service.CallGuardianService" ... />`, but the Kotlin file `android/app/src/main/java/org/suraksha/sms/service/CallGuardianService.kt` has not been implemented.
  - **Dual Architecture Disconnect:** The `android/` directory was originally constructed as a native Kotlin Android app for SMS scanning (`MainActivity.kt`), whereas the fraud dashboard is a web application in `frontend/`. A unified bridge (WebView or Capacitor BridgeActivity) is required to merge background SMS protection with the real-time Call Guardian interface.
  - **Host Toolchain Limitation:** Neither `java` nor `javac` nor the Android SDK is installed on the host system PATH, preventing command-line execution of `./gradlew assembleDebug` directly on this machine without a local JDK.

---

### 1.6 Security, Privacy & Session Management
* **Current State:**
  - Zero audio chunks written to disk in the primary WebSocket stream.
  - Rolling in-memory PCM buffer capped at **30 seconds (960 KB)** to eliminate memory accumulation.
  - Full memory wipe upon session closure (`sess.pcm_buffer.clear()`).
  - Stale sessions (> 15 min inactive) automatically purged.
  - 100% offline verification in Airplane mode.
* **Identified Gaps & Deficiencies:**
  - Missing upload file size limit (enforce 25 MB max on `/api/detect/call` and 2 MB max on `/api/calls/stream-chunk`).
  - Need a startup orphan-file cleaner to wipe any residual files left in `backend/data/` from previous server restarts.

---

## 2. Summary of Findings & Action Plan

| Component | Status | Risk / Gap | Action Required in Phase 7 |
| :--- | :---: | :--- | :--- |
| **WebSocket API** | ✅ Working | Missing `audio_warning_chg` in WS payload | Add `audio_warning_chg` in `main.py` payload |
| **HTTP Endpoints** | ⚠️ Gap | No upload file size limit (DoS risk) | Add 25 MB limit & HTTP 413 rejection |
| **Temp Storage** | ⚠️ Gap | Crash-orphaned temp files | Add startup cleanup routine for `backend/data/` |
| **Detection Engine**| ⚠️ Gap | Missing `audio_warning_chg` in return dict | Add Chhattisgarhi spoken alert generator |
| **Dialect Dataset** | ⚠️ Gap | 20 scenarios need real-world expansion | Construct expanded 40+ scenario rural dataset |
| **Android Service** | ❌ Missing| `CallGuardianService.kt` not implemented | Implement Kotlin foreground service with notification |
| **Android Bridge** | ⚠️ Gap | Native SMS vs Web UI separation | Connect WebView / Capacitor bridge |
| **Build Toolchain** | ⚠️ Gap | No local JDK on host PATH | Provide standalone build guide & Gradle sync |

---

## 3. Recommended Sequential Implementation Stages

1. **Stage 1 (Complete):** Technical audit, gap localization, and action plan documentation (`PHASE7_AUDIT.md`).
2. **Stage 2:** Android native implementation:
   - Create `CallGuardianService.kt` with persistent notification channel and microphone lifecycle.
   - Configure Android WebView integration to host the Jan Suraksha dashboard inside the native app.
   - Document complete Android build instructions and Gradle sync requirements.
3. **Stage 3:** Real-world Chhattisgarhi dataset expansion (40+ scenarios covering 5 divisions, noisy audio, code-switching, and ambiguous edge cases) and automated benchmarking.
4. **Stage 4:** Rural user experience accessibility audit and assisted mode verification.
5. **Stage 5:** Security hardening: upload limits (25MB), orphaned file startup cleaners, and input sanitization.
6. **Stage 6:** Full regression testing and final documentation generation (`PHASE7_IMPLEMENTATION_REPORT.md`, `ANDROID_BUILD_GUIDE.md`, `REAL_WORLD_VALIDATION_REPORT.md`).
