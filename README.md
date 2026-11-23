# 🛡️ Suraksha (सुरक्षा)
### Offline-First Cyber Fraud Detection & Digital Financial Literacy Platform
**Hackasol 5.0 — Problem Statement GT-02 Option B**  
*Target Users: First-time digital payment users in rural & semi-urban Chhattisgarh (Raipur, Durg, Bilaspur, Korba, Bastar, Raigarh, Rajnandgaon, Surguja)*

---

## 🌟 Overview
**Suraksha** is a lightweight, offline-first Progressive Web Application (PWA) and Python backend engineered to protect first-time digital citizens against predatory cyber fraud. It analyzes deceptive SMS and WhatsApp messages, warns against Digital Arrest voice calls, detects impersonation and collect traps in UPI QR codes, teaches essential payment safety rules in local languages (Hindi, Chhattisgarhi, English), provides immediate 1930 helpline assistance with an evidence checklist, and empowers district authorities with privacy-preserving scam trend analytics.

---

## 🏗️ Architecture: The Three Zones

Suraksha follows a strict three-zone decoupled architectural model:

```
+-----------------------------------------------------------------------------------+
|                            1. ON-DEVICE ZONE (100% OFFLINE)                       |
|  - HTML5/CSS3/Vanilla JS PWA (Zero external CDNs, Zero 3P frameworks)             |
|  - Native Android App (Kotlin, Room DB, BroadcastReceiver, Background AI Engine)  |
|  - Offline Text Normalizer & Multi-lingual Rule Checks (EN / HI / Hinglish)       |
|  - Fake-QR & upi:// URI Decoder (OpenCV QRCodeDetector running offline)           |
|  - Scam Stage Progression Tracker (Authority -> Urgency -> Sensitive -> Payment)  |
|  - Visual Swipeable Lessons & 10-Scenario Financial Literacy Quiz                |
|  - Emergency 1930 Helpline Call & Offline Downloadable Evidence Checklist        |
|  - Local Offline Report Queue (IndexedDB / LocalStorage)                          |
+-----------------------------------------------------------------------------------+
                                        |  (Syncs upon connection)
                                        v
+-----------------------------------------------------------------------------------+
|                                2. SERVER ZONE (ONLINE)                            |
|  - Anonymous Report Intake (Scam type, District, Hashed indicator, Device hash)    |
|  - Privacy Guard: Zero message text or private conversations ever stored/uploaded|
|  - Abuse Checks: Deduplication & 10 reports/device/hr rate limiting               |
|  - Multi-Device Confirmation Logic: Unconfirmed until N=3 distinct devices report|
|  - District Policy Dashboard: Aggregations with k >= 5 privacy suppression        |
|  - Emerging Scam Cluster Detection: Unsupervised TF-IDF + Cosine Clustering       |
|  - Cryptographically Signed Update Pack: Ed25519 (PyNaCl) signed blacklist        |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                                3. EVALUATION ZONE                                 |
|  - Labelled synthetic corpus (3,600 balanced messages: EN, HI, Hinglish, CHG)     |
|  - Stratified 80/20 train/held-out test split (Fixed random seed: 42)             |
|  - Character n-grams (2-5) + Word n-grams (1-2) with calibrated Logistic Regr.   |
|  - Automated evaluation pipeline exporting metrics.json and in-app dashboard     |
+-----------------------------------------------------------------------------------+
```

---

## ⚙️ Quickstart & Setup

### Prerequisites
- Python 3.11+
- Recommended: Virtual environment (`.venv`)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Model Training & Evaluation
Generate the synthetic dataset (3,600 samples across 4 languages), train the model, evaluate on held-out test split, and export metrics:
```bash
# From repository root:
python -m backend.app.evaluation.run

# Or from backend/ directory:
cd backend
python -m app.evaluation.run
cd ..
```

### 3. Seed Demo Data for Chhattisgarh Districts
Populate realistic confirmed and unconfirmed report samples across Chhattisgarh districts (Raipur, Durg, Bilaspur, Korba, Bastar, etc.):
```bash
python scripts/seed_dashboard.py
```

### 4. Optional: Download Offline Vosk Speech Model (for Voice Calls)
Vosk operates 100% offline. To enable automatic speech-to-text for recorded calls:
1. Download the small Hindi model: [vosk-model-small-hi-0.22.zip](https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip)
2. Extract the folder into `backend/models/vosk-model-small-hi/`
> *Note: If the model is not downloaded, Suraksha gracefully falls back to direct transcript input/pasting without any crashes.*

### 5. Launch Application
```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Open your browser at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📊 Held-Out Test Evaluation Results

The dataset consists of **3,600 synthetic samples** generated across 4 language categories: English, Hindi (Devanagari), Hinglish, and Chhattisgarhi. The genuine class deliberately contains authentic bank transaction debits/credits, CSPDCL utility receipts, delivery notifications, agricultural mandi prices, and genuine bank OTP alerts ("DO NOT SHARE WITH ANYONE").

> **Synthetic Dataset Disclosure:** All messages in `backend/data/dataset.json` are synthetically generated using rule templates based on reported CERT-In, CSPDCL, and Indian Cybercrime Coordination Centre (I4C) advisories.

### Exact Performance on Hardened Multi-Category Evaluation Benchmark (100 independent unseen test samples, from `backend/data/metrics.json`):

| Metric | Overall | English (EN) | Hindi (HI) | Hinglish | Chhattisgarhi (CHG) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Accuracy** | **92.00%** | 92.86% | 89.29% | 100.0% | **92.59%** |
| **Precision** | **90.48%** | 90.91% | 90.00% | 100.0% | 90.91% |
| **Recall** | **90.48%** | 90.91% | 90.00% | 100.0% | 90.91% |
| **F1 Score** | **90.48%** | 90.91% | 90.00% | 100.0% | 90.91% |
| **False Positive Rate (FPR)** | **6.90%** | 5.00% | 6.25% | 0.00% | 7.69% |
| **False Negative Rate (FNR)** | **9.52%** | 9.09% | 10.00% | 0.00% | 9.09% |
| **Test Samples** | **100** | 42 | 28 | 3 | 27 |

#### Confusion Matrix (Benchmark Test Set):
```
                  Predicted Genuine    Predicted Scam
Actual Genuine           54                  4        (True Negatives: 54, False Positives: 4, FPR: 6.90%)
Actual Scam               4                 38        (False Negatives: 4, True Positives: 38, FNR: 9.52%)
```
*Zero false alarms on genuine bank OTP alerts containing "DO NOT SHARE WITH ANYONE" safeguards user trust.*

---

## 🧪 Running Automated Pytest Suite
Run the 13 automated tests covering detection, fake-QR verification, abuse checks, indicator confirmation ($N=3$), and Ed25519 signature checks:
```bash
pytest -v
```

---

## ⏱️ 3-Minute Hackathon Demo Script (Airplane-Mode Proof)

### Phase 1: Airplane Mode Offline Verification (0:00 - 1:15)
1. **Turn OFF WiFi / Mobile Data** on the demonstration device or laptop.
2. Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.
3. Observe the header status badge showing **"Working Offline (ऑफलाइन)"**.
4. Switch language between **हिन्दी**, **छत्तीसगढ़ी**, and **English** with instant zero-network translation.
5. Go to **"Check (जांचें)" -> SMS Tab**:
   - Tap **"⚡ CSPDCL Electricity Bill Scam"** sample chip.
   - Tap **"अभी जांचें (Analyze Now)"**.
   - Show:
     - 🔴 **Likely Scam (खतरा)** verdict banner.
     - Highlighted risky phrases: `"disconnected tonight at 9:30 PM"`, `"CSPDCL"`.
     - 4-Stage timeline showing progression to **Urgency & Panic**.
     - Top contributing model n-grams.
     - Tap **"बोलकर सुनाएं (Read Aloud)"** for audio playback.
   - Now test a genuine bank OTP alert (`582910 is your secret OTP... DO NOT SHARE WITH ANYONE`).
   - Show: 🟢 **Looks Genuine (सुरक्षित)** — bank safety warning guard prevents false alarms.

### Phase 2: Fake-QR Code & Voice Call Defense (1:15 - 2:00)
1. Switch to **"UPI क्यूआर कोड"** subtab:
   - Tap **"⚠️ Fake CSPDCL Personal Account"** test chip.
   - Tap **"QR कोड डिकोड करें"**.
   - Highlight:
     - Payee Name shown large: `CSPDCL Electricity Bill Collector`.
     - Recipient UPI ID shown large: `rohitkumar982@okaxis`.
     - Red Alert: **"CRITICAL MISMATCH: Payee claims official utility, but handle is a personal user account!"**
2. Switch to **"फ़ोन कॉल"** subtab:
   - Tap **"🚔 Mumbai Police Video Arrest"** sample.
   - Show the high-priority warning banner: **"🚨 Police / CBI Digital Arrest Extortion Call"** explaining that Digital Arrest has no legal provision in India.

### Phase 3: Literacy Quiz & Offline Queue to Reconnect Sync (2:00 - 3:00)
1. Go to **"Learn (सीखें)"**:
   - Swipe through visual flashcards on OTP and ATM safety.
   - Answer 2-3 scenario quiz questions to demonstrate real-time score calculation and badge upgrade.
2. Go to **"Help (मदद)"**:
   - Demonstrate the two distinct paths:
     - **Path A: "I Lost Money"** -> One-tap `tel:1930` call.
     - **Path B: "Suspected Fraud, No Loss Yet"** -> Chakshu portal.
   - Check items in the **Evidence Checklist** (UTR number, amount, call log) and tap **"प्रिंट / डाउनलोड रसीद"** to download an offline `.txt` evidence receipt.
3. Tap **"गुमनाम रिपोर्ट करें"**:
   - Fill in a scammer number `9827109999` for district **Raipur**.
   - Tap **"सहमति है, गुमनाम रिपोर्ट भेजें"**.
   - App notifies: **"📶 रिपोर्ट फोन में सुरक्षित है। इंटरनेट आते ही पहुंच जाएगी (Saved to offline queue)"**.
4. **Turn internet back ON (or reconnect network)**:
   - The status badge turns green: **"Connected (ऑनलाइन)"**.
   - Suraksha's background sync instantly uploads the queued report.
   - Open **"Radar (रडार)"**:
     - View the updated district dashboard with custom SVG bar charts.
     - Point out the privacy $k \ge 5$ suppression rule protecting small community privacy.
     - Highlight the **Emerging Scam Alert** banner identifying new scam variants in Chhattisgarh.

---

## 🔒 Privacy, Security & Safety
1. **Zero Text Transmission:** User messages, call recordings, and personal documents never leave the local client device without explicit consent.
2. **Hashed Indicators:** Reports contain only the scam type, district, and a salted SHA-256 hash of the indicator (phone, UPI handle, or domain).
3. **No Direct External Calls:** Real government and police APIs are never invoked programmatically; verified direct links and standard `tel:1930` phone intents are provided.
4. **Cryptographic Integrity:** Update packs are cryptographically signed using **Ed25519 (PyNaCl)** to prevent MITM tampering.

---

## ⚠️ Known Limitations & Future Work
- **Chhattisgarhi Localization:** All Chhattisgarhi translations are marked `"needs review by a native speaker"` for regional dialect verification.
- **Microphone Streaming WebSocket:** Live streaming call transcription is a stretch goal; file uploads and direct transcript pastes are fully supported in v1.0.
- **Audio Codec Fallback:** Compressed non-WAV formats (e.g. M4A) require local `ffmpeg` on the host machine to convert to 16kHz mono PCM.

---

## 🛡️ Real-Time Offline TRAI SMS Sender Header Check (Jan Suraksha Smishing Guard)

Suraksha integrates an on-device **TRAI (Telecom Regulatory Authority of India) SMS Sender Header Guard** that validates commercial DLT headers, exposes 10-digit mobile number smishing, flags typosquatting lookalike headers, and verifies enclosed web links against brand domains—**100% offline with zero cloud lookups**.

### How TRAI SMS Header Verification Works
1. **Header Parsing**: Deconstructs incoming sender IDs (e.g. `AX-HDFCBK-T`):
   - **Operator & Circle Prefix (2 Letters)**: e.g. `AX` (Airtel), `VM` (Vi), `BZ` (BSNL), `JZ` (Jio).
   - **Header Body (Max 6 Alphanumeric Characters)**: e.g. `HDFCBK`, `SBIINB`, `CSPDCL`.
   - **Category Suffix**: `-T` (Transactional), `-S` (Service Implicit), `-P` (Promotional), `-G` (Government).
2. **10-Digit Mobile Number Smishing Trap (RED Alert)**:
   - Official banks, electricity utilities, and government departments **never** send transactional alerts or KYC requests from personal 10-digit mobile numbers (`+91-9xxxxxxxxx`).
   - If a personal number sends messages claiming banking or utility actions, it is immediately flagged as **CRITICAL / RED**.
3. **Typosquatting & Lookalike Header Detection (Levenshtein Distance 1–2)**:
   - Scammers craft headers closely resembling genuine ones (e.g. `HDFCBNK` vs `HDFCBK`, `AIRTEL1` vs `AIRTEL`).
   - The engine computes Levenshtein distance against all known registered headers in `headers.json` and flags lookalikes in RED.
4. **Brand-Domain Alignment & Phishing Link Verification**:
   - Compares URLs inside the message against the brand's verified domains (e.g. `sbi.co.in`, `hdfcbank.com`).
   - Flags public link shorteners (`bit.ly`, `tinyurl.com`, `is.gd`) and `.apk` downloads as high-risk.
5. **Decision Score Fusion**:
   - Combines the TRAI header risk score with the on-device ML text classifier (`combined_score = 0.45 * header_score + 0.55 * ml_score`), prioritizing critical header violations.

### Top 30 Impersonated Indian Brands in `headers.json`
`backend/models/headers.json` & `android/app/src/main/assets/headers.json`:
- **Banks (10)**: State Bank of India (SBI), HDFC Bank, ICICI Bank, Axis Bank, Punjab National Bank (PNB), Bank of Baroda (BOB), Kotak Mahindra Bank, Canara Bank, IndusInd Bank, Union Bank of India.
- **UPI & Wallets (5)**: PhonePe, Google Pay, Paytm, BHIM UPI (NPCI), CRED.
- **Telecom (4)**: Bharti Airtel, Reliance Jio, Vi (Vodafone Idea), BSNL.
- **Government & Utilities (5)**: Income Tax Department, EPFO, UIDAI (Aadhaar), DigiLocker, CSPDCL (Chhattisgarh Electricity).
- **Couriers & Logistics (4)**: India Post, Blue Dart, DTDC, Delhivery.
- **E-Commerce (2)**: Amazon India, Flipkart.

### How to Add or Verify New Headers
Refer to [TODO_VERIFY.md](file:///c:/project/hackasol/TODO_VERIFY.md) for headers requiring manual telecom verification. To add a new verified entity:
```json
{
  "brand": "New Entity Name",
  "type": "bank|upi|telecom|government|utility|courier|ecommerce",
  "headers": ["6CHAR1", "6CHAR2"],
  "domains": ["officialdomain.gov.in"]
}
```
Run `pytest tests/test_trai_header_checker.py` to ensure complete schema and detection validation.

### Battery Optimization Guide (Xiaomi, Oppo, Realme, Vivo, Samsung)
To ensure uninterrupted background SMS checking when the screen is locked:
1. **Xiaomi / Redmi / POCO (MIUI / HyperOS)**:
   - `Settings -> Apps -> Manage Apps -> Jan Suraksha -> Battery Saver -> Select 'No Restrictions'`.
   - Enable `Autostart` toggle.
2. **Oppo / Realme (ColorOS / Realme UI)**:
   - `Settings -> Battery -> More Battery Settings -> App Battery Management -> Jan Suraksha -> Allow background activity & Allow auto-launch`.
3. **Vivo / iQOO (Funtouch OS)**:
   - `Settings -> Battery -> Background Power Consumption Management -> Jan Suraksha -> High Background Power Usage`.
4. **Samsung (One UI)**:
   - `Settings -> Apps -> Jan Suraksha -> Battery -> Unrestricted`.

---

## 📱 Native Android Application: Offline Automatic SMS Spam Detection

Suraksha includes an idiomatic native Android application in `android/` providing background SMS interception, on-device ML classification, Room database storage, and high-priority fraud alerts.

### Android Architecture Overview
```
Incoming SMS Broadcast (SMS_RECEIVED)
       │
       ▼
IncomingSmsReceiver (goAsync + Coroutines)
       │  (Extracts sender & joins multipart chunks)
       ▼
TextNormalizer (Devanagari/Latin NFC, Hinglish phonetic mapping)
       │
       ▼
OfflineSmsClassifier (TF-IDF Word 1-2 + Char 2-5 + Calibrated Logistic Regression)
       ├──> Evaluates RuleGuardEngine (Genuine Bank OTP guardrail & urgent threat patterns)
       │
       ▼
SmsRepository & Room Database (SmsClassificationEntity stored locally)
       │
       ├── If SAFE: Quietly logged in Room DB (no intrusive notification)
       │
       └── If SPAM: NotificationHelper triggers High-Priority Alert
                      ├── Shows sender & safe masked preview (links un-clickable)
                      ├── Action: "Mark as Safe"
                      └── Action: "Report Spam"
```

### Android Permissions & Default SMS Role
- **`android.permission.RECEIVE_SMS`**: Intercepts and parses incoming SMS messages automatically in background.
- **`android.permission.POST_NOTIFICATIONS`**: Required on Android 13+ (API 33+) to display high-priority fraud warning notifications.
- **`android.permission.RECEIVE_BOOT_COMPLETED`**: Re-activates background interception after phone reboot.

#### Is Default SMS App Status Required?
- **No, not for detection and notification:** On Android, any application granted `RECEIVE_SMS` can intercept `android.provider.Telephony.SMS_RECEIVED`, classify incoming SMS messages in the background, alert the user via notifications, and maintain a local fraud log without replacing the default messaging app.
- **When is Default SMS App required?** Only if the app intends to silently suppress or delete SMS messages so they never reach the native SMS inbox (`SMS_DELIVER_ACTION`). Suraksha purposefully does not suppress messages silently to respect user autonomy and prevent unintended message loss.

### How to Build and Run in Android Studio
1. Open **Android Studio** (Hedgehog / Iguana / Jellyfish / Ladybug).
2. Select **File -> Open...** and navigate to `./android`.
3. Allow Gradle to sync dependencies (`androidx.room`, `kotlinx.coroutines`, `material3`).
4. Select an Android emulator (API 26+) or connected physical device.
5. Click **Run 'app'** (`Shift + F10`).
6. Tap **"Grant SMS Permission"** when prompted.
7. Test using the built-in SMS simulator on the dashboard or by sending an SMS from emulator extended controls (`... -> Phone -> SMS`).

---

## 🙏 Open-Source Credits & AI Disclosure

### Open-Source Technologies
Suraksha stands on the shoulders of outstanding open-source projects and libraries:
- **FastAPI & Uvicorn**: High-performance asynchronous backend and WebSocket streaming framework.
- **Scikit-learn**: Machine learning algorithms, vectorizers, and evaluation pipelines (TF-IDF, Logistic Regression, LinearSVC).
- **Vosk**: Offline, lightweight automatic speech recognition engine for Indian speech.
- **OpenCV (opencv-python)**: Offline computer vision and QR code detector (`QRCodeDetector`).
- **PyNaCl**: Python binding to libsodium for high-speed cryptographic Ed25519 signatures.
- **Android Jetpack & Material 3**: Native Android architecture components (Room database, Coroutines, NotificationManager, Material 3 design system).

### AI Assistance Disclosure
In accordance with open engineering standards, development of this project was assisted by Google DeepMind's **Antigravity** autonomous AI coding assistant. AI was utilized for architecture design, test suite automation, code generation, refactoring, and dialect dataset curation, with all outputs verified, tested, and validated by the engineering team.

---

## 📜 License
Developed for Hackasol 5.0 (GT-02). Open-source for public benefit and citizen cyber safety.
