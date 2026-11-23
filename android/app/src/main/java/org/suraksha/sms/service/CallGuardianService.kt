package org.suraksha.sms.service

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import org.suraksha.sms.R
import org.suraksha.sms.ui.MainActivity

/**
 * CallGuardianService: Persistent Foreground Service for Real-Time Offline Audio Call Protection.
 * Runs during an active call listening session to ensure the operating system does not kill the
 * microphone audio monitoring thread under memory pressure.
 *
 * Enforces microphone foreground service standards required by Android 14+ (API 34+).
 */
class CallGuardianService : Service() {

    companion object {
        private const val TAG = "CallGuardianService"
        private const val NOTIFICATION_ID = 2001
        const val CHANNEL_ID = "call_guardian_channel"
        const val CHANNEL_NAME = "Call Guardian Protection"

        const val ACTION_START = "org.suraksha.sms.action.START_CALL_GUARDIAN"
        const val ACTION_STOP = "org.suraksha.sms.action.STOP_CALL_GUARDIAN"
        const val EXTRA_LANGUAGE = "extra_language"

        @Volatile
        private var running = false

        fun isServiceRunning(): Boolean = running

        fun start(context: Context, language: String = "hi") {
            val intent = Intent(context, CallGuardianService::class.java).apply {
                action = ACTION_START
                putExtra(EXTRA_LANGUAGE, language)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stop(context: Context) {
            val intent = Intent(context, CallGuardianService::class.java).apply {
                action = ACTION_STOP
            }
            context.startService(intent)
        }
    }

    private var audioManager: AudioManager? = null
    private var audioFocusRequest: AudioFocusRequest? = null
    private var currentLanguage: String = "hi"

    private val audioFocusChangeListener = AudioManager.OnAudioFocusChangeListener { focusChange ->
        when (focusChange) {
            AudioManager.AUDIOFOCUS_LOSS -> {
                Log.w(TAG, "Audio focus lost permanently")
            }
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT -> {
                Log.d(TAG, "Audio focus lost temporarily")
            }
            AudioManager.AUDIOFOCUS_GAIN -> {
                Log.d(TAG, "Audio focus regained")
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "CallGuardianService created")
        createNotificationChannel()
        audioManager = getSystemService(Context.AUDIO_SERVICE) as? AudioManager
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action ?: ACTION_START
        currentLanguage = intent?.getStringExtra(EXTRA_LANGUAGE) ?: "hi"

        when (action) {
            ACTION_STOP -> {
                Log.i(TAG, "Received STOP action")
                stopForegroundService()
                return START_NOT_STICKY
            }
            ACTION_START -> {
                // 1. Verify runtime RECORD_AUDIO permission
                if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                    != PackageManager.PERMISSION_GRANTED) {
                    Log.e(TAG, "RECORD_AUDIO permission not granted; aborting CallGuardianService")
                    stopSelf()
                    return START_NOT_STICKY
                }

                // 2. Prevent duplicate service execution
                if (running) {
                    Log.d(TAG, "CallGuardianService already running, updating notification")
                    val notif = buildForegroundNotification()
                    val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                    manager.notify(NOTIFICATION_ID, notif)
                    return START_STICKY
                }

                running = true
                requestAudioFocus()

                // 3. Promote to foreground service with microphone type
                val notification = buildForegroundNotification()
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    val serviceType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                        ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
                    } else {
                        ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
                    }
                    startForeground(NOTIFICATION_ID, notification, serviceType)
                } else {
                    startForeground(NOTIFICATION_ID, notification)
                }

                Log.i(TAG, "CallGuardianService running in foreground (language: $currentLanguage)")
            }
        }

        return START_STICKY
    }

    private fun requestAudioFocus() {
        try {
            audioManager?.let { am ->
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    val attrs = AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ASSISTANCE_SONIFICATION)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build()

                    audioFocusRequest = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
                        .setAudioAttributes(attrs)
                        .setOnAudioFocusChangeListener(audioFocusChangeListener)
                        .build()

                    audioFocusRequest?.let { am.requestAudioFocus(it) }
                } else {
                    @Suppress("DEPRECATION")
                    am.requestAudioFocus(
                        audioFocusChangeListener,
                        AudioManager.STREAM_VOICE_CALL,
                        AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK
                    )
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Could not request audio focus: ${e.message}")
        }
    }

    private fun abandonAudioFocus() {
        try {
            audioManager?.let { am ->
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    audioFocusRequest?.let { am.abandonAudioFocusRequest(it) }
                } else {
                    @Suppress("DEPRECATION")
                    am.abandonAudioFocus(audioFocusChangeListener)
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Error abandoning audio focus: ${e.message}")
        }
    }

    private fun buildForegroundNotification(): Notification {
        val tapIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingTap = PendingIntent.getActivity(
            this,
            0,
            tapIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0)
        )

        val stopIntent = Intent(this, CallGuardianService::class.java).apply {
            action = ACTION_STOP
        }
        val pendingStop = PendingIntent.getService(
            this,
            1,
            stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0)
        )

        val title = when (currentLanguage) {
            "chg" -> "कॉल सुरक्षा कवच सक्रिय हे"
            "en" -> "Call Guardian Active"
            else -> "रीयल-टाइम AI कॉल सुरक्षा कवच सक्रिय"
        }

        val content = when (currentLanguage) {
            "chg" -> "माइक्रोफ़ोन सुनत हे। गोठ-बात म खतरा दिखे ले तुरंत चेतावनी मिलही। (कॉल स्पीकर म राखव)"
            "en" -> "Microphone active. AI scanning for scams in real time. (Keep call on speakerphone)"
            else -> "माइक्रोफ़ोन सक्रिय है। संदिग्ध बातचीत पर AI तुरंत चेतावनी देगा। (कॉल स्पीकर पर रखें)"
        }

        val stopBtnText = when (currentLanguage) {
            "chg" -> "सुरक्षा बंद करव"
            "en" -> "Stop Protection"
            else -> "सुरक्षा बंद करें"
        }

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle(title)
            .setContentText(content)
            .setStyle(NotificationCompat.BigTextStyle().bigText(content))
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .setContentIntent(pendingTap)
            .addAction(R.drawable.ic_delete, stopBtnText, pendingStop)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Ongoing notification displayed while AI Call Guardian is actively protecting against scam calls."
                setShowBadge(false)
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    private fun stopForegroundService() {
        running = false
        abandonAudioFocus()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
        Log.i(TAG, "CallGuardianService stopped and cleaned up")
    }

    override fun onDestroy() {
        super.onDestroy()
        stopForegroundService()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
