# Jan Suraksha Android APK Build & Deployment Guide

This guide documents the architecture, prerequisites, compilation commands, and deployment instructions for building the native Android APK (`org.suraksha.sms`) incorporating the SMS guardian, Call Guardian foreground service, and the full offline Cyber Shield web dashboard.

---

## 1. Architecture Overview

Jan Suraksha employs a hybrid high-performance architecture:

```
+--------------------------------------------------------------------------+
|                       Jan Suraksha Android App                            |
+--------------------------------------------------------------------------+
|  Native Layer (Kotlin)             |  Local WebView Layer (HTML5/JS/WASM) |
|  - BootReceiver & IncomingSmsReceiver|  - WebViewAssetLoader (Secure Local) |
|  - OfflineSmsClassifier & RuleGuard |  - 100% On-Device Scam Evaluation     |
|  - CallGuardianService (Foreground) |  - UPI QR Threat Inspection Engine   |
|  - SurakshaNativeBridge (JS Bridge)|  - Pre-cached Local Audio Warnings   |
+--------------------------------------------------------------------------+
                               |
                   [SurakshaNativeBridge]
              - Vibrate (Haptic Motor)
              - Start / Stop Call Guardian Service
              - Emergency Helpline Dialing (1930)
              - Native SMS Shield Status
```

### Key Components

1. **`CallGuardianService.kt`**
   - Implements `FOREGROUND_SERVICE_TYPE_MICROPHONE`.
   - Displays a persistent, localized ongoing notification with an instant "सुरक्षा बंद करें (Stop)" action button.
   - Manages audio focus requests and drops cleanly on lifecycle termination.
2. **`SurakshaNativeBridge.kt`**
   - Safely exposes hardware control (`vibrate()`, `startCallGuardian()`, `stopCallGuardian()`, `dialEmergencyHelpline()`, `isSmsProtectionActive()`) to the WebView dashboard via `window.SurakshaNative`.
3. **`WebViewAssetLoader`**
   - Serves local files from `android/app/src/main/assets/public/` using the secure `https://appassets.androidplatform.net/assets/public/` virtual domain, eliminating CORS and mixed-content issues.
4. **Dual-View UI (`activity_main.xml`)**
   - Top toolbar allows users and security administrators to toggle seamlessly between the **Full Cyber Shield Web Dashboard** and the **Native SMS History & Inspection** view.

---

## 2. Audio Capture Boundary: Realities of Android Cellular Streams

> [!IMPORTANT]
> **Android OS Telephony Isolation & Speakerphone Requirement:**
> Standard Android security architecture (enforced since Android 6.0 and hardened in Android 10/11/12/13/14) strictly isolates cellular voice calls. Non-system applications cannot tap the private cellular downlink stream (`VOICE_CALL` / `VOICE_DOWNLINK`) without OEM platform keys or root privileges.
>
> **How Jan Suraksha Operates in Real-World Scenarios:**
> - **Speakerphone Mode:** When a suspicious incoming call is answered on speakerphone, `CallGuardianService` listens via the device microphone (`RECORD_AUDIO`), providing immediate real-time transcription and visual/audio warnings.
> - **Recorded Audio & Voicemail Verification:** Users can inspect suspicious audio clips or call recordings offline through the dashboard file analyzer.

---

## 3. Build Prerequisites

Before compiling the APK, ensure your workstation or CI environment has:

1. **Java Development Kit (JDK):**
   - JDK 17 (recommended: Eclipse Temurin 17 or OpenJDK 17).
   - Set environment variable: `JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-17..."` (or Linux `/usr/lib/jvm/java-17-openjdk`).
   - Add `%JAVA_HOME%\bin` to system `PATH`.
2. **Android SDK:**
   - SDK Command-Line Tools & Platform Tools (`adb`).
   - Compile SDK: `34` (Android 14).
   - Target SDK: `34`.
   - Min SDK: `26` (Android 8.0 Oreo).
   - Set environment variable: `ANDROID_HOME="C:\Users\<user>\AppData\Local\Android\Sdk"`.
3. **Python 3.10+:**
   - For synchronizing web assets to the Android package.

---

## 4. Step-by-Step Compilation Instructions

### Step 4.1: Synchronize Frontend Web Assets
Ensure all dashboard files, scripts, styles, and synthesized audio alert files are updated in the Android assets public folder:

```bash
# In project root (c:\project\hackasol)
python scripts/sync_assets_to_android.py
```

*Expected output:* `[+] Synchronized 53 files (~8.3 MB) to .../assets/public`

### Step 4.2: Build Debug APK via Gradle

#### On Windows (PowerShell / CMD):
```powershell
cd android
.\gradlew.bat assembleDebug
```

#### On Linux / macOS:
```bash
cd android
chmod +x ./gradlew
./gradlew assembleDebug
```

#### Clean Build (if updating native resources):
```bash
cd android
.\gradlew.bat clean assembleDebug
```

### Step 4.3: Locate Output APK
Upon a successful build, the debug APK is generated at:
```
android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 5. Device Installation & Verification

### Step 5.1: Install via ADB
Connect an Android device with Developer Mode & USB Debugging enabled:

```bash
adb devices
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

### Step 5.2: Grant Runtime Permissions
On first launch, the app prompts for permissions. You can also grant them via ADB:

```bash
adb shell pm grant org.suraksha.sms android.permission.RECEIVE_SMS
adb shell pm grant org.suraksha.sms android.permission.RECORD_AUDIO
adb shell pm grant org.suraksha.sms android.permission.POST_NOTIFICATIONS
```

### Step 5.3: Test Native SMS Scanner
Send a simulated scam SMS to the device:
```bash
adb emu sms send "+919876543210" "Dear SBI User, your YONO account is blocked. Update PAN immediately: http://bit.ly/sbi-fake"
```
Verify that:
1. `IncomingSmsReceiver` intercepts and scores the message.
2. A high-priority heads-up warning notification appears.
3. The message is cataloged in the Native SMS History table.

### Step 5.4: Test Call Guardian Foreground Service
1. In the app, switch to the Cyber Shield Dashboard.
2. Tap **"कॉल सुनना शुरू करें (Start Listening)"**.
3. Verify that:
   - The microphone icon activates.
   - A persistent notification appears in the notification drawer: **"कॉल सुरक्षा चालू है (Call Guardian Active)"**.
   - Haptic vibration confirms activation.
   - Tapping **"सुरक्षा बंद करें (Stop)"** in the notification terminates the service cleanly.

---

## 6. Release Build Preparation (Signing)

To build a release-ready APK/AAB for Google Play or direct distribution:

1. Generate a keystore:
   ```bash
   keytool -genkey -v -keystore suraksha-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias suraksha
   ```
2. Configure `android/key.properties` (do not commit this file):
   ```properties
   storePassword=your_keystore_password
   keyPassword=your_key_password
   keyAlias=suraksha
   storeFile=../suraksha-release-key.jks
   ```
3. Run release assemble:
   ```bash
   cd android
   .\gradlew.bat assembleRelease
   ```
