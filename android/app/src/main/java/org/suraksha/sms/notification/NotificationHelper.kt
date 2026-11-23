package org.suraksha.sms.notification

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import org.suraksha.sms.R
import org.suraksha.sms.data.db.SmsClassificationEntity
import org.suraksha.sms.ui.MainActivity

object NotificationHelper {

    private const val CHANNEL_ID = "suraksha_spam_alerts"
    private const val CHANNEL_NAME = "Suraksha Fraud & Spam Warnings"
    private const val CHANNEL_DESC = "Instant offline warnings when suspicious fraud or spam SMS is intercepted."

    const val ACTION_MARK_SAFE = "org.suraksha.sms.ACTION_MARK_SAFE"
    const val ACTION_MARK_SPAM = "org.suraksha.sms.ACTION_MARK_SPAM"
    const val EXTRA_SMS_ID = "extra_sms_id"

    fun createNotificationChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val importance = NotificationManager.IMPORTANCE_HIGH
            val channel = NotificationChannel(CHANNEL_ID, CHANNEL_NAME, importance).apply {
                description = CHANNEL_DESC
                enableVibration(true)
                setShowBadge(true)
            }
            val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    fun showSpamAlert(context: Context, entity: SmsClassificationEntity, confidencePercent: Int) {
        createNotificationChannel(context)

        // Safe preview: Truncate message and prevent accidental link clicking
        val safePreview = if (entity.messageBody.length > 90) {
            entity.messageBody.substring(0, 87) + "..."
        } else {
            entity.messageBody
        }

        // Tap intent to open MainActivity with detection details
        val openIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra(EXTRA_SMS_ID, entity.id)
        }
        val openPendingIntent = PendingIntent.getActivity(
            context,
            entity.id.toInt(),
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // Action 1: Mark as Safe
        val markSafeIntent = Intent(context, MainActivity::class.java).apply {
            action = ACTION_MARK_SAFE
            putExtra(EXTRA_SMS_ID, entity.id)
        }
        val markSafePending = PendingIntent.getActivity(
            context,
            (entity.id * 10 + 1).toInt(),
            markSafeIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // Action 2: 1930 Helpline Call Action
        val dial1930Intent = Intent(Intent.ACTION_DIAL).apply {
            data = android.net.Uri.parse("tel:1930")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        val dial1930Pending = PendingIntent.getActivity(
            context,
            (entity.id * 10 + 2).toInt(),
            dial1930Intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // Action 3: Alert Family / Share warning
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_SUBJECT, "⚠️ साइबर फ्रॉड चेतावनी (Cyber Scam Alert)")
            putExtra(Intent.EXTRA_TEXT, "सावधान! मुझे इस नंबर (${entity.senderNumber}) से संदेहास्पद फ्रॉड संदेश मिला है: '${safePreview}'. किसी लिंक पर क्लिक न करें। जन सुरक्षा ऐप द्वारा सतर्कता संदेश।")
        }
        val sharePending = PendingIntent.getActivity(
            context,
            (entity.id * 10 + 3).toInt(),
            Intent.createChooser(shareIntent, "परिवार को सचेत करें"),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_spam_warning)
            .setContentTitle("🚨 संदेहास्पद SMS चेतावनी (${entity.senderNumber})")
            .setContentText(safePreview)
            .setStyle(
                NotificationCompat.BigTextStyle()
                    .setBigContentTitle("🚨 ठगी की चेतावनी: ${entity.senderNumber}")
                    .bigText("संदेश:\n\"$safePreview\"\n\nकारण: TRAI हेडर असंगति या अनधिकृत वित्तीय दावा। किसी लिंक पर क्लिक न करें।")
            )
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setColor(ContextCompat.getColor(context, R.color.color_danger))
            .setContentIntent(openPendingIntent)
            .setAutoCancel(true)
            .addAction(0, "📞 1930 कॉल करें", dial1930Pending)
            .addAction(0, "👨‍👩‍👧 परिवार को बताएं", sharePending)
            .build()

        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(entity.id.toInt(), notification)
    }
}
