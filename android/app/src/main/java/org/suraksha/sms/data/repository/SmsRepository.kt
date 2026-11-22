package org.suraksha.sms.data.repository

import android.content.Context
import androidx.lifecycle.LiveData
import org.suraksha.sms.data.db.SmsClassificationDao
import org.suraksha.sms.data.db.SmsClassificationEntity
import org.suraksha.sms.data.db.SurakshaDatabase
import org.suraksha.sms.data.model.UserFeedback
import org.suraksha.sms.ml.OfflineSmsClassifier
import org.suraksha.sms.ml.PredictionResult

class SmsRepository(
    private val dao: SmsClassificationDao,
    private val classifier: OfflineSmsClassifier
) {

    val allClassifications: LiveData<List<SmsClassificationEntity>> = dao.getAllLive()
    val spamCount: LiveData<Int> = dao.getSpamCountLive()
    val safeCount: LiveData<Int> = dao.getSafeCountLive()
    val totalCount: LiveData<Int> = dao.getTotalCountLive()

    suspend fun processIncomingSms(sender: String, messageBody: String): Pair<SmsClassificationEntity, PredictionResult> {
        val prediction = classifier.classify(messageBody)
        
        val entity = SmsClassificationEntity(
            senderNumber = sender.ifBlank { "Unknown Sender" },
            messageBody = messageBody,
            classification = prediction.classification.name,
            predictionScore = prediction.probabilityScore,
            timestamp = System.currentTimeMillis(),
            userFeedback = UserFeedback.NONE.name,
            detectedRules = prediction.matchedRules.joinToString(", ")
        )

        val insertedId = dao.insert(entity)
        val savedEntity = entity.copy(id = insertedId)

        return Pair(savedEntity, prediction)
    }

    suspend fun updateFeedback(id: Long, feedback: UserFeedback) {
        dao.updateFeedback(id, feedback.name)
    }

    suspend fun clearHistory() {
        dao.clearAll()
    }

    fun isModelReady(): Boolean = classifier.isReady()

    fun getModelFeaturesCount(): Int = classifier.getFeatureCount()

    companion object {
        @Volatile
        private var INSTANCE: SmsRepository? = null

        fun getInstance(context: Context): SmsRepository {
            return INSTANCE ?: synchronized(this) {
                val db = SurakshaDatabase.getDatabase(context)
                val classifier = OfflineSmsClassifier(context)
                val instance = SmsRepository(db.smsDao(), classifier)
                INSTANCE = instance
                instance
            }
        }
    }
}
