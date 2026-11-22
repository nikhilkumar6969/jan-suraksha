package org.suraksha.sms.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey
import org.suraksha.sms.data.model.ClassificationType
import org.suraksha.sms.data.model.UserFeedback

@Entity(tableName = "sms_classifications")
data class SmsClassificationEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val senderNumber: String,
    val messageBody: String,
    val classification: String, // "SPAM", "SAFE", "UNSURE"
    val predictionScore: Float, // 0.0 to 1.0 confidence
    val timestamp: Long = System.currentTimeMillis(),
    val userFeedback: String = UserFeedback.NONE.name, // "NONE", "MARKED_SAFE", "MARKED_SPAM"
    val detectedRules: String = "" // Comma-separated rule tags e.g. "OTP_GUARD, DIGITAL_ARREST"
)
