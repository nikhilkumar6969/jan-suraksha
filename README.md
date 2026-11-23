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

### Exact Performance on Held-Out Test Set (80/20 Stratified Split, 720 test samples, Seed=42, from `backend/data/metrics.json`):

| Metric | Overall | English (EN) | Hindi (HI) | Hinglish | Chhattisgarhi (CHG) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Accuracy** | **85.56%** | 83.89% | 87.22% | 83.33% | **87.78%** |
| **Precision** | **89.75%** | 90.67% | 86.81% | 91.67% | 90.48% |
| **Recall** | **80.28%** | 75.56% | 87.78% | 73.33% | 84.44% |
| **F1 Score** | **84.75%** | 82.42% | 87.29% | 81.48% | 87.36% |
| **False Positive Rate (FPR)** | **9.17%** | 7.78% | 13.33% | 6.67% | 8.89% |
| **Test Samples** | **720** | 180 | 180 | 180 | 180 |

#### Confusion Matrix (Held-out Test Split):
```
                  Predicted Genuine    Predicted Scam
Actual Genuine           327                 33       (True Negatives: 327, False Positives: 33)
Actual Scam               71                289       (False Negatives: 71, True Positives: 289)
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
