# Jan Suraksha — Phase 8: Deployment Pipeline, CI/CD Cloud APK Builder & Village Kiosk Mode Report

**Project:** Jan Suraksha (जन सुरक्षा) — Offline Scam & Cyber Fraud Shield for Chhattisgarh  
**Phase:** Phase 8 (Deployment Readiness, Automated Cloud CI/CD & CSC Assisted Kiosk Mode)  
**Date:** 2026-11-23  
**Status:** COMPLETED & VERIFIED (46/46 Tests Passing)  

---

## 1. Executive Summary

Phase 8 expands Jan Suraksha's operational delivery model across two vital dimensions:
1. **Automated CI/CD Cloud Build Pipeline:** A turnkey GitHub Actions workflow (`.github/workflows/ci.yml`) that runs backend regression suites and automatically builds, packages, and archives the Android APK (`app-debug.apk`) in the cloud with JDK 17 and Android SDK command-line tools on every commit/push.
2. **Village Kiosk & Common Service Centre (CSC / Choice Centre) Assisted Mode:** A specialized operational mode designed for Village Level Entrepreneurs (VLEs), Panchayat operators, and cyber volunteers assisting non-literate or elderly villagers who may not own smartphones. It provides high-contrast assisted navigation, a one-click printable/downloadable **Citizen Cyber Safety Advisory Slip (नागरिक साइबर सुरक्षा परामर्श पावती)** with official State Government branding and unique reference ID, and an offline Gram Panchayat incident log with CSV export for local police / Cyber Cell escalation.

---

## 2. Key Deliverables & Architecture

### A. Automated GitHub Actions CI/CD Pipeline (`.github/workflows/ci.yml`)
- **Triggers:** Automated execution on every `push` to `main`, `pull_request` targeting `main`, and manual dispatch (`workflow_dispatch`).
- **Job 1: Backend Regression & Dialect Tests (`test-backend`):**
  - Environment: `ubuntu-latest`, Python 3.11.
  - Validates full 46-test regression suite covering real-time call audio, Chhattisgarhi dialect benchmarks, UPI QR forensics, Ed25519 signature checks, and ASR fallbacks.
- **Job 2: Android APK Builder (`build-android`):**
  - Environment: `ubuntu-latest`, Temurin JDK 17, Android SDK tools.
  - Grants executable permissions to Gradle wrapper (`chmod +x android/gradlew`).
  - Executes `./gradlew assembleDebug --no-daemon --stacktrace`.
  - Verifies APK file size and computes SHA-256 checksum.
  - Automatically uploads the generated `app-debug.apk` as a GitHub Actions artifact (30-day retention).

### B. Village Kiosk & CSC Assisted Mode
- **Operator Toggle (`#btnToggleKiosk`):** Prominently placed in the civic utility bar. Toggling switches the application into high-contrast, large-touch operator mode with sticky top status banner (`#kioskTopBanner`).
- **Citizen Cyber Safety Advisory Slip (`#advisoryReceiptModalOverlay`):**
  - Official Government of Chhattisgarh header, Tiranga insignia, and unique reference ID (e.g. `JS-CG-202611-L4B3H`).
  - Risk assessment badge (`HIGH RISK SCAM` vs. `SAFE`), scam category, and confidence score.
  - Analyzed message snippet and specific threat indicators detected.
  - Actionable instructions for the citizen (Do not transfer funds, verify with nearest Substation/Bank, dial 1930).
  - Print-optimized CSS (`@media print`) designed for both thermal receipt printers and standard A4/A5 office printers.
  - Offline `.txt` voucher download for Bluetooth transfer to basic mobile phones.
- **Offline Gram Panchayat Incident Log (`#kioskLogModalOverlay`):**
  - Stores up to 50 recent assisted citizen checks locally in `localStorage` without collecting personal citizen identifiers (zero PII storage).
  - One-click CSV export (`JanSuraksha_Kiosk_Log_YYYY-MM-DD.csv`) for formal reporting to Thana / District Cyber Crime Cell.

### C. Offline PWA & Asset Synchronization
- **Service Worker (`sw.js`):** Bumped cache version to `suraksha-v2.2`, incorporating `kiosk.js`.
- **Android Public Assets:** Fully synchronized to `android/app/src/main/assets/public/` (67 files, 12.54 MB).
- **Multilingual Support:** Vernacular translations added to `hi.json`, `chg.json`, and `en.json`.

---

## 3. Test & Verification Matrix

| Suite | Component | Result | Latency / Metric |
| :--- | :--- | :---: | :---: |
| Backend Regression | Pytest (46/46 unit tests) | **PASSED** | 20.37s |
| Dialect Benchmark | 42 Chhattisgarhi scenarios | **PASSED** | 100% Precision, 100% Recall |
| Browser Subagent | Kiosk Toggle & Banner Display | **VERIFIED** | Active banner rendered |
| Browser Subagent | Advisory Slip Modal Generation | **VERIFIED** | Ref ID `JS-CG-202611-L4B3H` |
| Asset Sync | `android/app/src/main/assets/public/` | **VERIFIED** | 67 files synchronized |

**Visual Verification Artifact:**  
[Browser Evidence Screenshot](file:///C:/Users/jt332/.gemini/antigravity/brain/ca6f95e8-59f6-4aaa-b581-cd90a43d307d/final_step_418.png)

---

## 4. Summary of Modified Files

- `.github/workflows/ci.yml` *(New CI/CD workflow)*
- `frontend/js/kiosk.js` *(New Kiosk & Advisory Manager)*
- `frontend/index.html` *(Kiosk toggle, banner, receipt and log modals)*
- `frontend/css/app.css` *(Kiosk styles and `@media print` thermal formatting)*
- `frontend/js/app.js` *(Kiosk subsystem initialization)*
- `frontend/js/detector.js` *(Receipt generation hook from SMS verdict)*
- `frontend/sw.js` *(Service Worker v2.2 caching)*
- `frontend/locales/en.json` *(English strings)*
- `frontend/locales/hi.json` *(Hindi strings)*
- `frontend/locales/chg.json` *(Chhattisgarhi strings)*
- `android/gradlew` *(Executable permission bit set)*
- `android/app/src/main/assets/public/*` *(Synchronized assets)*
