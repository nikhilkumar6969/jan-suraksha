package org.suraksha.sms.data.repository

import android.content.Context
import androidx.lifecycle.LiveData
import org.suraksha.sms.data.db.SmsClassificationDao
import org.suraksha.sms.data.db.SmsClassificationEntity
import org.suraksha.sms.data.db.SurakshaDatabase
import org.suraksha.sms.data.model.ClassificationType
import org.suraksha.sms.data.model.UserFeedback
import org.suraksha.sms.ml.HeaderRiskLevel
import org.suraksha.sms.ml.OfflineSmsClassifier
import org.suraksha.sms.ml.PredictionResult
import org.suraksha.sms.ml.TraiHeaderGuard

class SmsRepository(
    private val dao: SmsClassificationDao,
    private val classifier: OfflineSmsClassifier,
    private val context: Context? = null
) {

    val allClassifications: LiveData<List<SmsClassificationEntity>> = dao.getAllLive()
    val spamCount: LiveData<Int> = dao.getSpamCountLive()
    val safeCount: LiveData<Int> = dao.getSafeCountLive()
    val totalCount: LiveData<Int> = dao.getTotalCountLive()

    suspend fun processIncomingSms(sender: String, messageBody: String): Pair<SmsClassificationEntity, PredictionResult> {
        val mlPrediction = classifier.classify(messageBody)
        
        // Evaluate offline TRAI Header Guard if Context is available
        var finalClassification = mlPrediction.classification
        var finalScore = mlPrediction.probabilityScore
        var finalConfidence = mlPrediction.confidencePercent
        val allRules = mlPrediction.matchedRules.toMutableList()
        var explanation = mlPrediction.explanation

        context?.let { ctx ->
            val headerRes = TraiHeaderGuard.checkSender(ctx, sender, messageBody)
            if (headerRes.reasons.isNotEmpty()) {
                allRules.addAll(headerRes.reasons)
            }

            if (headerRes.level == HeaderRiskLevel.RED) {
                finalClassification = ClassificationType.SPAM
                finalScore = maxOf(finalScore, headerRes.score)
                finalConfidence = maxOf(finalConfidence, (headerRes.score * 100).toInt())
                explanation = headerRes.explanationHi
            } else if (headerRes.level == HeaderRiskLevel.AMBER && finalClassification == ClassificationType.SAFE) {
                finalScore = maxOf(finalScore, headerRes.score)
                explanation = headerRes.explanationHi
            }
        }

        val combinedPrediction = mlPrediction.copy(
            classification = finalClassification,
            probabilityScore = finalScore,
            confidencePercent = finalConfidence,
            matchedRules = allRules.distinct(),
            explanation = explanation
        )

        val entity = SmsClassificationEntity(
            senderNumber = sender.ifBlank { "Unknown Sender" },
            messageBody = messageBody,
            classification = combinedPrediction.classification.name,
            predictionScore = combinedPrediction.probabilityScore,
            timestamp = System.currentTimeMillis(),
            userFeedback = UserFeedback.NONE.name,
            detectedRules = combinedPrediction.matchedRules.joinToString(", ")
        )

        val insertedId = dao.insert(entity)
        val savedEntity = entity.copy(id = insertedId)

        return Pair(savedEntity, combinedPrediction)
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
                val instance = SmsRepository(db.smsDao(), classifier, context.applicationContext)
                INSTANCE = instance
                instance
            }
        }
    }
}
