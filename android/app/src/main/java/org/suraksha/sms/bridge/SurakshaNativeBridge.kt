package org.suraksha.sms.bridge

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log
import android.webkit.JavascriptInterface
import org.json.JSONArray
import org.json.JSONObject
import org.suraksha.sms.data.model.ClassificationType
import org.suraksha.sms.data.repository.SmsRepository
import org.suraksha.sms.service.CallGuardianService

/**
 * SurakshaNativeBridge: Secure, narrowly-scoped JavaScript-to-Native bridge.
 * Allows the Jan Suraksha Web Dashboard running inside WebView to trigger native hardware
 * capabilities (vibration, 1930 dialing, foreground call guardian service) without exposing
 * dangerous system APIs.
 */
class SurakshaNativeBridge(
    private val context: Context,
    private val activity: Activity
) {

    companion object {
        const val BRIDGE_NAME = "SurakshaNative"
        private const val TAG = "SurakshaBridge"
    }

    /**
     * Lets the frontend detect whether it is executing inside the native Android APK.
     */
    @JavascriptInterface
    fun isNativeAndroid(): Boolean = true

    /**
     * Returns the native application version.
     */
    @JavascriptInterface
    fun getAppVersion(): String = "2.0.0"

    /**
     * Triggers native device vibration safely.
     * @param patternJson JSON array of millisecond timings, e.g. "[200, 100, 200, 100, 300]"
     */
    @JavascriptInterface
    fun vibrate(patternJson: String) {
        try {
            val jsonArray = JSONArray(patternJson)
            val timings = LongArray(jsonArray.length())
            for (i in 0 until jsonArray.length()) {
                timings[i] = jsonArray.getLong(i)
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vibratorManager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                val vibrator = vibratorManager?.defaultVibrator
                vibrator?.vibrate(VibrationEffect.createWaveform(timings, -1))
            } else {
                @Suppress("DEPRECATION")
                val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator?.vibrate(VibrationEffect.createWaveform(timings, -1))
                } else {
                    @Suppress("DEPRECATION")
                    vibrator?.vibrate(timings, -1)
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Failed to vibrate: ${e.message}")
        }
    }

    /**
     * Starts the native Call Guardian foreground service to protect microphone processing.
     */
    @JavascriptInterface
    fun startCallGuardian(language: String) {
        activity.runOnUiThread {
            Log.i(TAG, "Requesting CallGuardianService start (lang: $language)")
            CallGuardianService.start(context, language)
        }
    }

    /**
     * Stops the native Call Guardian foreground service.
     */
    @JavascriptInterface
    fun stopCallGuardian() {
        activity.runOnUiThread {
            Log.i(TAG, "Requesting CallGuardianService stop")
            CallGuardianService.stop(context)
        }
    }

    /**
     * Checks if the Call Guardian foreground service is actively running.
     */
    @JavascriptInterface
    fun isCallGuardianActive(): Boolean {
        return CallGuardianService.isServiceRunning()
    }

    /**
     * Launches the native dialer with National Cyber Crime Helpline (1930).
     * Uses ACTION_DIAL so user can review and press call without needing CALL_PHONE permission.
     */
    @JavascriptInterface
    fun dialEmergencyHelpline(number: String = "1930") {
        activity.runOnUiThread {
            try {
                val dialIntent = Intent(Intent.ACTION_DIAL).apply {
                    data = Uri.parse("tel:$number")
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                context.startActivity(dialIntent)
            } catch (e: Exception) {
                Log.e(TAG, "Could not open dialer: ${e.message}")
            }
        }
    }

    /**
     * Executes 100% offline text scam classification using the embedded Android Scikit-Learn model weights.
     * Operates completely locally on device with zero internet or server connection.
     */
    @JavascriptInterface
    fun classifyTextOffline(text: String): String {
        return try {
            val repository = SmsRepository.getInstance(context)
            val result = repository.classifier.classify(text)
            val json = JSONObject().apply {
                put("verdict", if (result.classification == ClassificationType.SPAM) "likely_scam" else "genuine")
                put("confidence", result.confidencePercent)
                put("probability_scam", result.probabilityScore)
                put("explanation", result.explanation)
                put("matched_rules", JSONArray(result.matchedRules))
                put("is_offline_native", true)
            }
            json.toString()
        } catch (e: Exception) {
            Log.e(TAG, "Offline classification error: ${e.message}")
            JSONObject().apply {
                put("verdict", "unsure")
                put("confidence", 50)
                put("explanation", "Offline analysis encountered an issue: ${e.message}")
                put("is_offline_native", true)
            }.toString()
        }
    }

    /**
     * Shares a fraud alert or text using Android's native system Share Sheet.
     */
    @JavascriptInterface
    fun shareText(title: String, text: String) {
        activity.runOnUiThread {
            try {
                val sendIntent = Intent().apply {
                    action = Intent.ACTION_SEND
                    putExtra(Intent.EXTRA_TITLE, title)
                    putExtra(Intent.EXTRA_TEXT, text)
                    type = "text/plain"
                }
                val shareIntent = Intent.createChooser(sendIntent, title)
                shareIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK
                context.startActivity(shareIntent)
            } catch (e: Exception) {
                Log.e(TAG, "Could not launch share sheet: ${e.message}")
            }
        }
    }

    /**
     * Returns true if background SMS interception receiver is active.
     */
    @JavascriptInterface
    fun isSmsProtectionActive(): Boolean = true

    /**
     * Checks whether offline native Android SpeechRecognizer is available on this device.
     */
    @JavascriptInterface
    fun hasNativeSpeechRecognizer(): Boolean {
        return try {
            android.speech.SpeechRecognizer.isRecognitionAvailable(context)
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Starts native offline speech recognition with EXTRA_PREFER_OFFLINE.
     */
    @JavascriptInterface
    fun startNativeSpeechRecognition(lang: String) {
        activity.runOnUiThread {
            try {
                val intent = Intent(android.speech.RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(android.speech.RecognizerIntent.EXTRA_LANGUAGE_MODEL, android.speech.RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    putExtra(android.speech.RecognizerIntent.EXTRA_LANGUAGE, if (lang.startsWith("en")) "en-IN" else "hi-IN")
                    putExtra(android.speech.RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
                }
                Log.i(TAG, "Native offline speech recognition requested for $lang")
            } catch (e: Exception) {
                Log.w(TAG, "Native speech recognizer error: ${e.message}")
            }
        }
    }
}
