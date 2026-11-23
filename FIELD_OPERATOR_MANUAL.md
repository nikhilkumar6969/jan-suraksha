# Jan Suraksha — Village Kiosk & Field Operator Manual (ग्राम पंचायत एवं चॉइस सेंटर ऑपरेटर संदर्शिका)

**Project:** Jan Suraksha (जन सुरक्षा) — Offline Scam & Cyber Fraud Shield for Chhattisgarh  
**Target Audience:** Village Level Entrepreneurs (VLEs), CSC / Choice Centre Operators, Gram Panchayat Secretaries, and Cyber Mitras  
**Language:** English & Hindi (द्विभाषी संदर्शिका)  
**Version:** 2.0 (Production Release)  

---

## 1. Overview & Operational Mandate (उद्देश्य एवं दायित्व)

In rural Chhattisgarh, opportunistic cyber criminals prey upon farmers, women, and elderly citizens using fake **CSPDCL electricity disconnection threats**, **Mahtari Vandan / PM-Kisan bonus frauds**, and **fake police/CBI digital arrest extortion**. Because internet connectivity in interior villages (Bastar, Surguja, Gariaband) can be intermittent, **Jan Suraksha is engineered to run 100% offline on local kiosk hardware**.

As a Village Operator or Cyber Mitra:
- You are the first line of defense for your Gram Panchayat.
- You operate the assisted kiosk interface to evaluate suspicious messages, QR codes, and phone calls.
- You provide elderly and non-literate villagers with a clear verbal explanation and an official **Citizen Cyber Safety Advisory Slip (नागरिक सुरक्षा पावती)**.

---

## 2. 100% Offline Kiosk Setup (कियोस्क सेटअप)

### Step 1: Launch Jan Suraksha
1. On your kiosk laptop, desktop, or tablet, open **Google Chrome**, **Edge**, or the **Jan Suraksha Android App**.
2. Navigate to your local server address (e.g. `http://localhost:8000` or open the installed PWA from your desktop/home screen).
3. Verify the top status badge shows **"Working Offline (ऑफलाइन)"** or **"Connected (ऑनलाइन)"**.

### Step 2: Activate CSC Operator Mode (कियोस्क मोड सक्रिय करें)
1. In the top civic bar, click the **🏛️ कियोस्क मोड (CSC)** pill button.
2. The top banner will expand with the title:
   > **🏛️ चॉइस सेंटर / CSC ऑपरेटर मोड — ग्रामीण नागरिक सहायता एवं ऑफलाइन सुरक्षा पावती प्रणाली**
3. The layout automatically switches into large-type, high-contrast assisted mode suited for shared monitors and elderly citizens.

### Step 3: Verify Audio Speakers
1. Navigate to **Check (जांचें) -> Voice Call (कॉल)**.
2. Under *"ऑफ़लाइन क्षेत्रीय आवाज़ चेतावनी टेस्ट"*, click the test buttons:
   - `⚠️ UPI PIN चेतावनी`
   - `🚨 डिजिटल अरेस्ट चेतावनी`
   - `🏦 बैंक KYC चेतावनी`
3. Confirm that audio alerts play loudly and clearly in the selected regional language (Hindi or Chhattisgarhi).

---

## 3. Citizen Inquiry Workflows (नागरिक जांच प्रक्रिया)

### Scenario A: Suspicious SMS, WhatsApp Message, or Lottery Link
1. Ask the villager to show their phone or read the incoming SMS.
2. Type or paste the message text into the **"Check (जांचें) -> Message (SMS)"** box.
3. Click **Analyze Now (जांचें)**.
4. If flagged as **"Likely Scam (खतरा / Risk)"**:
   - The screen turns bold red with a distinct vibration and audio chime.
   - Click **"बोलकर सुनाएं"** so the villager can hear the explanation in their language.
   - Click **"परामर्श पावती (प्रिंट / PDF)"**.
   - An official Chhattisgarh Government advisory slip will appear with a unique reference number (e.g. `JS-CG-202611-X9XL5`).
   - Click **"🖨️ पावती प्रिंट करें"** to print on your thermal slip printer or A4 printer, and hand it to the citizen.
   - Alternatively, click **"📥 टेक्स्ट पावती (.txt)"** to send via Bluetooth to the citizen's feature phone.

### Scenario B: Threatening Phone Call (Digital Arrest / Bijli Cut / Police Threat)
1. **Live Incoming Call:**
   - Instruct the villager to immediately put the incoming call on **Loudspeaker (Speakerphone)**.
   - In Jan Suraksha, open **"Check -> Voice Call"** and click **"Start Real-Time Guardian (लाइव सुरक्षा चालू करें)"**.
   - The on-device AI listens in 3-second streaming windows without recording or storing the private audio.
   - If extortion, OTP, or arrest demands are heard, the screen flashes **CRITICAL THREAT** and plays a vernacular voice command: *"Savdhaan! Yeh farzi call hai, turant phone kaatein!"*
2. **Audio File or Recording Check:**
   - If the villager recorded the call, click **"Choose Audio File"** or test with one of the built-in sample clips:
     - `⚡ CSPDCL Bijli Cut Call (.wav)`
     - `Digital Arrest Call (.wav)`
     - `Bank KYC Block Call (.wav)`
     - `🌾 Kisan Mandi Dhan Call (.wav) [Safe Negative Control]`

### Scenario C: Suspicious UPI QR Code (दूध डेयरी, खाद बीज दुकान या लाटरी)
1. Navigate to **"Check -> UPI QR Code"**.
2. Scan the printed QR code using the webcam or upload a photo of the QR sticker.
3. The offline computer vision engine decodes the `upi://pay` URI:
   - Flags suspicious personal Gmail/Hotmail handles disguised as official state bodies (e.g. `cspdcl.bill@okhdfcbank`).
   - Verifies whether the QR forces an immediate auto-debit amount without merchant name verification.

---

## 4. Emergency "Golden Hour" Protocol (पैसे कटने पर आपातकालीन कदम)

If a villager arrives at your CSC stating that money was fraudulently deducted from their bank account:

```
[FRAUD OCCURRED]
       │
       ▼ (Within 1 to 2 Hours — "Golden Hour")
1. DIAL 1930 IMMEDIATELY
       │
       ▼
2. RETRIEVE 12-DIGIT BANK UTR NUMBER
   (Found in bank debit SMS: "Rs. X debited... UTR: 432109876543")
       │
       ▼
3. REQUEST IMMEDIATE ACCOUNT LIEN / FREEZE
   (Cyber police coordinate with receiving bank to stop cash withdrawal)
       │
       ▼
4. FORMAL REPORTING
   - Visit https://cybercrime.gov.in
   - Open Jan Suraksha "Help (मदद)" -> Print Thana & Bank Application Draft
```

> **IMPORTANT RULE:** Every minute counts. Do NOT wait to visit the police station before calling 1930. The cyber cell can freeze funds only while the money is in transit between digital wallets and accounts.

---

## 5. Village Record Keeping & Police Escalation (ग्राम पंचायत रजिस्टर)

In Kiosk Mode, Jan Suraksha automatically records an anonymized incident log for every assisted consultation:
1. In the top kiosk banner, click **"📋 ग्राम पंचायत परामर्श लॉग"**.
2. View the table of recent inquiries (Reference ID, Date, Category, Risk Level, Confidence).
3. Click **"📥 CSV रिपोर्ट डाउनलोड करें"** at the end of each month.
4. Save the file `JanSuraksha_Kiosk_Log_YYYY-MM-DD.csv` and share it with the Gram Panchayat Secretary or Thana In-Charge during monthly crime prevention meetings.

---

## 6. Technical Support & Offline Integrity

- **Rule Pack Validity:** Always check the top strip: *"Ed25519 Verified"*. This guarantees the on-device blacklist and scam rules have not been tampered with.
- **Data Privacy:** Jan Suraksha does NOT upload citizen phone numbers, private audio, or raw message text to any cloud server. Everything runs strictly on local device memory.
