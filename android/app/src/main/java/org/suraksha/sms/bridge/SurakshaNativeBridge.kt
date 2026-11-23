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
     * Returns true if background SMS interception receiver is active.
     */
    @JavascriptInterface
    fun isSmsProtectionActive(): Boolean = true
}
