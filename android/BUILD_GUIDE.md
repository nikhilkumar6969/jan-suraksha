# 📱 Suraksha Android Application — Build & Compilation Guide

**Package Name:** `org.suraksha.sms`  
**Target SDK:** 34 (Android 14) | **Min SDK:** 26 (Android 8.0 Oreo)  
**Kotlin:** 1.9.22 | **Java Version:** 17 | **Gradle Plugin:** 8.3.0  

---

## 🛠️ Prerequisites

To build the APK on Windows, Linux, or macOS:

1. **Java Development Kit (JDK) 17:**
   - Install Eclipse Temurin 17 or OpenJDK 17:
     ```bash
     # Windows (via winget):
     winget install EclipseAdoptium.Temurin.17.JDK
     ```
   - Set `JAVA_HOME`:
     ```powershell
     $env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.x-hotspot"
     $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
     ```

2. **Android Command-Line Tools & SDK Platform 34:**
   - Set `ANDROID_HOME`:
     ```powershell
     $env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
     ```
   - Required components:
     - `platforms;android-34`
     - `build-tools;34.0.0`

---

## 🚀 Building Debug APK

From repository root:
```bash
cd android
.\gradlew.bat assembleDebug
```

On Linux / macOS:
```bash
cd android
./gradlew assembleDebug
```

Output APK will be generated at:
`android/app/build/outputs/apk/debug/app-debug.apk`

---

## 🔍 Verified Native Capabilities
- `CallGuardianService`: Persistent foreground service listening for real-time scam calls with offline Sherpa-ONNX/Vosk streaming.
- `SurakshaNativeBridge`: Full bi-directional JavaScript interface between Vanilla JS PWA and native Kotlin Room DB / telephony providers.
- `SmsReceiver`: Real-time on-device SMS interception and privacy-first analysis.
- `Public Assets`: Web assets bundled directly inside `app/src/main/assets/public/` for 100% offline, zero-network execution.
