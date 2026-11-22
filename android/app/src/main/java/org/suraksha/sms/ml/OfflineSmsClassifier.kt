package org.suraksha.sms.ml

import android.content.Context
import org.json.JSONObject
import org.suraksha.sms.data.model.ClassificationType
import java.io.BufferedReader
import java.io.InputStreamReader
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.sqrt

data class PredictionResult(
    val classification: ClassificationType,
    val probabilityScore: Float, // 0.0 to 1.0 (probability of SPAM)
    val confidencePercent: Int,   // 0 to 100
    val matchedRules: List<String>,
    val explanation: String,
    val isModelLoaded: Boolean
)

class OfflineSmsClassifier(private val context: Context? = null) {

    private var intercept: Double = 0.0
    private var wordFeatures = HashMap<String, FloatArray>() // [idf, coef]
    private var charFeatures = HashMap<String, FloatArray>() // [idf, coef]
    private var isLoaded = false

    init {
        context?.let { loadModelFromAssets(it) }
    }

    @Synchronized
    fun loadModelFromAssets(ctx: Context): Boolean {
        if (isLoaded) return true

        return try {
            val inputStream = ctx.assets.open("scam_model_weights.json")
            val reader = BufferedReader(InputStreamReader(inputStream, "UTF-8"))
            val sb = StringBuilder()
            var line: String?
            while (reader.readLine().also { line = it } != null) {
                sb.append(line)
            }
            reader.close()

            loadModelFromJson(sb.toString())
        } catch (e: Exception) {
            e.printStackTrace()
            isLoaded = false
            false
        }
    }

    @Synchronized
    fun loadModelFromJson(jsonString: String): Boolean {
        return try {
            val root = JSONObject(jsonString)
            intercept = root.optDouble("intercept", 0.0)

            val wordsObj = root.getJSONObject("word_features")
            wordFeatures.clear()
            val wKeys = wordsObj.keys()
            while (wKeys.hasNext()) {
                val k = wKeys.next()
                val arr = wordsObj.getJSONArray(k)
                wordFeatures[k] = floatArrayOf(arr.getDouble(0).toFloat(), arr.getDouble(1).toFloat())
            }

            val charsObj = root.getJSONObject("char_features")
            charFeatures.clear()
            val cKeys = charsObj.keys()
            while (cKeys.hasNext()) {
                val k = cKeys.next()
                val arr = charsObj.getJSONArray(k)
                charFeatures[k] = floatArrayOf(arr.getDouble(0).toFloat(), arr.getDouble(1).toFloat())
            }

            isLoaded = true
            true
        } catch (e: Exception) {
            e.printStackTrace()
            isLoaded = false
            false
        }
    }

    fun isReady(): Boolean = isLoaded

    fun getFeatureCount(): Int = wordFeatures.size + charFeatures.size

    fun classify(messageBody: String): PredictionResult {
        if (messageBody.isBlank()) {
            return PredictionResult(
                classification = ClassificationType.SAFE,
                probabilityScore = 0.0f,
                confidencePercent = 100,
                matchedRules = emptyList(),
                explanation = "Empty message text.",
                isModelLoaded = isLoaded
            )
        }

        val normalized = TextNormalizer.normalize(messageBody)

        // 1. Rule Engine Evaluation
        val ruleResult = RuleGuardEngine.evaluate(normalized)

        // 2. ML Inference (if model loaded)
        var mlProbSpam = 0.5f

        if (isLoaded) {
            // A. Word Features (TF-IDF sublinear + L2 norm)
            val wordCounts = TextNormalizer.extractWordNgrams(normalized)
            var wNormSq = 0.0
            var wDot = 0.0

            for ((term, cnt) in wordCounts) {
                val weights = wordFeatures[term]
                if (weights != null) {
                    val idf = weights[0].toDouble()
                    val coef = weights[1].toDouble()
                    val tf = 1.0 + ln(cnt.toDouble())
                    val value = tf * idf
                    wNormSq += value * value
                    wDot += value * coef
                }
            }
            val wScore = if (wNormSq > 0.0) (wDot / sqrt(wNormSq)) else 0.0

            // B. Char Features (TF-IDF sublinear + L2 norm)
            val charCounts = TextNormalizer.extractCharNgrams(normalized, 2, 5)
            var cNormSq = 0.0
            var cDot = 0.0

            for ((term, cnt) in charCounts) {
                val weights = charFeatures[term]
                if (weights != null) {
                    val idf = weights[0].toDouble()
                    val coef = weights[1].toDouble()
                    val tf = 1.0 + ln(cnt.toDouble())
                    val value = tf * idf
                    cNormSq += value * value
                    cDot += value * coef
                }
            }
            val cScore = if (cNormSq > 0.0) (cDot / sqrt(cNormSq)) else 0.0

            // C. Combined Logit & Sigmoid Probability
            val logit = wScore + cScore + intercept
            mlProbSpam = (1.0 / (1.0 + exp(-logit))).toFloat()
        }

        // 3. Rule Overrides & Safety Guards
        var finalClassification: ClassificationType
        var finalScore: Float
        val explanation: String

        if (ruleResult.isGenuineBankAlert && !ruleResult.isExplicitOtpDemand) {
            // Guardrail: Authentic bank security alerts warning NOT to share OTP
            finalClassification = ClassificationType.SAFE
            finalScore = 0.02f
            explanation = "Authentic bank transaction/security alert with explicit 'DO NOT SHARE' warning."
        } else if (ruleResult.isExplicitOtpDemand) {
            finalClassification = ClassificationType.SPAM
            finalScore = 0.98f
            explanation = "High risk: Message attempts to solicit secret OTP or banking credentials."
        } else if (ruleResult.isDigitalArrest) {
            finalClassification = ClassificationType.SPAM
            finalScore = 0.98f
            explanation = "Severe threat: Impersonating law enforcement with 'Digital Arrest' extortion."
        } else if (ruleResult.isFakeKycOrBillCut && ruleResult.hasSuspiciousLink) {
            finalClassification = ClassificationType.SPAM
            finalScore = 0.96f
            explanation = "Urgent power disconnection or bank suspension threat with suspicious phishing link."
        } else {
            // Based on calibrated ML probability
            if (mlProbSpam >= 0.50f) {
                finalClassification = ClassificationType.SPAM
                finalScore = mlProbSpam
                explanation = "Classified as Spam by local on-device ML model."
            } else {
                finalClassification = ClassificationType.SAFE
                finalScore = mlProbSpam
                explanation = "No malicious patterns detected. Message appears genuine."
            }
        }

        val confidence = if (finalClassification == ClassificationType.SPAM) {
            (finalScore * 100).toInt()
        } else {
            ((1.0f - finalScore) * 100).toInt()
        }

        return PredictionResult(
            classification = finalClassification,
            probabilityScore = finalScore,
            confidencePercent = confidence.coerceIn(50, 100),
            matchedRules = ruleResult.matchedRules,
            explanation = explanation,
            isModelLoaded = isLoaded
        )
    }
}
