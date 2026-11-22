package org.suraksha.sms.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.telephony.SmsMessage
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.suraksha.sms.data.model.ClassificationType
import org.suraksha.sms.data.repository.SmsRepository
import org.suraksha.sms.notification.NotificationHelper

class IncomingSmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val pendingResult = goAsync()

        CoroutineScope(Dispatchers.IO).launch {
            try {
                val messages: Array<SmsMessage>? = Telephony.Sms.Intents.getMessagesFromIntent(intent)
                if (messages.isNullOrEmpty()) return@launch

                // Group multipart SMS chunks by sender
                val senderToBodyMap = mutableMapOf<String, StringBuilder>()

                for (sms in messages) {
                    val sender = sms.displayOriginatingAddress ?: sms.originatingAddress ?: "Unknown"
                    val bodyChunk = sms.displayMessageBody ?: sms.messageBody ?: ""
                    
                    val sb = senderToBodyMap.getOrPut(sender) { StringBuilder() }
                    sb.append(bodyChunk)
                }

                val repository = SmsRepository.getInstance(context)

                for ((sender, bodyBuilder) in senderToBodyMap) {
                    val fullMessage = bodyBuilder.toString()
                    if (fullMessage.isBlank()) continue

                    // Offline ML + Rule Classification & Storage in Room
                    val (savedEntity, prediction) = repository.processIncomingSms(sender, fullMessage)

                    // Log detection without exposing full sensitive content
                    Log.d("SurakshaSms", "Classified SMS from $sender: ${prediction.classification} (Confidence: ${prediction.confidencePercent}%)")

                    if (prediction.classification == ClassificationType.SPAM) {
                        NotificationHelper.showSpamAlert(context, savedEntity, prediction.confidencePercent)
                    }
                }
            } catch (e: Exception) {
                Log.e("SurakshaSms", "Error processing incoming SMS", e)
            } finally {
                pendingResult.finish()
            }
        }
    }
}
