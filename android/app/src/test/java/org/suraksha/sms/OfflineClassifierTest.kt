package org.suraksha.sms

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.suraksha.sms.data.model.ClassificationType
import org.suraksha.sms.ml.OfflineSmsClassifier
import java.io.File

class OfflineClassifierTest {

    private lateinit var classifier: OfflineSmsClassifier

    @Before
    fun setUp() {
        classifier = OfflineSmsClassifier()
        // Load the exported model weights from assets directory
        val assetsFile = File("src/main/assets/scam_model_weights.json")
        val altPath = File("android/app/src/main/assets/scam_model_weights.json")
        
        val targetFile = when {
            assetsFile.exists() -> assetsFile
            altPath.exists() -> altPath
            else -> null
        }

        if (targetFile != null && targetFile.exists()) {
            val jsonContent = targetFile.readText(Charsets.UTF_8)
            classifier.loadModelFromJson(jsonContent)
        }
    }

    @Test
    fun testModelLoadsSuccessfully() {
        if (classifier.isReady()) {
            assertTrue("Expected model to be ready", classifier.isReady())
            assertTrue("Expected loaded features > 1000", classifier.getFeatureCount() > 1000)
        }
    }

    @Test
    fun testNormalGenuineSmsClassification() {
        val normalSms = "Hey Ramesh, are you attending the gram panchayat meeting tomorrow morning in Raipur?"
        val result = classifier.classify(normalSms)
        
        assertEquals(ClassificationType.SAFE, result.classification)
        assertTrue("Confidence should be >= 50%", result.confidencePercent >= 50)
    }

    @Test
    fun testGenuineBankOtpAlertGuard() {
        val bankOtp = "582910 is your secret One Time Password (OTP) for Rs 450 at Amazon. DO NOT SHARE WITH ANYONE. Bank never calls to ask OTP."
        val result = classifier.classify(bankOtp)
        
        assertEquals(ClassificationType.SAFE, result.classification)
        assertTrue("Expected genuine bank alert rule triggered", result.matchedRules.contains("GENUINE_BANK_GUARD"))
    }

    @Test
    fun testSpamElectricityScamClassification() {
        val scamSms = "URGENT: CSPDCL Electricity officer notice. Your power will be disconnected tonight at 9:30 PM due to unpaid bill of Rs 1,450. Call officer at 9876543210 immediately."
        val result = classifier.classify(scamSms)
        
        assertEquals(ClassificationType.SPAM, result.classification)
        assertTrue("Expected spam confidence >= 70%", result.confidencePercent >= 70)
    }

    @Test
    fun testDigitalArrestExtortionClassification() {
        val arrestSms = "CBI Cyber Crime Cell Notice: A parcel with drugs and passports found under your Aadhaar. You are placed under DIGITAL ARREST. Do not disconnect this call or tell anyone. Pay clearance bond immediately."
        val result = classifier.classify(arrestSms)
        
        assertEquals(ClassificationType.SPAM, result.classification)
        assertTrue("Expected digital arrest rule triggered", result.matchedRules.contains("DIGITAL_ARREST_EXTORTION"))
    }

    @Test
    fun testHinglishKycPhishingClassification() {
        val hinglishSms = "Dear user, aapka SBI YONO account block ho gaya hai. KYC update karne ke liye turant link bit.ly/sbi-kyc par click kare."
        val result = classifier.classify(hinglishSms)
        
        assertEquals(ClassificationType.SPAM, result.classification)
    }

    @Test
    fun testEmptyOrMalformedSms() {
        val emptyResult = classifier.classify("   ")
        assertEquals(ClassificationType.SAFE, emptyResult.classification)
        assertEquals(0.0f, emptyResult.probabilityScore, 0.001f)

        val malformedResult = classifier.classify("??? !!! ...")
        assertEquals(ClassificationType.SAFE, malformedResult.classification)
    }

    @Test
    fun testMultipartSmsConcatenation() {
        val part1 = "URGENT: CSPDCL Electricity notice. Your power will be disconnected "
        val part2 = "tonight at 9:30 PM due to unpaid bill. Call officer at 9876543210 immediately."
        val concatenated = part1 + part2
        
        val result = classifier.classify(concatenated)
        assertEquals(ClassificationType.SPAM, result.classification)
    }

    @Test
    fun testMissingModelGracefulFallback() {
        val uninitializedClassifier = OfflineSmsClassifier()
        assertFalse(uninitializedClassifier.isReady())
        
        // Rule guard should still evaluate even if ML weights file is uninitialized
        val scamWithRules = "Your account is locked. Share OTP with bank manager immediately."
        val res = uninitializedClassifier.classify(scamWithRules)
        assertEquals(ClassificationType.SPAM, res.classification)
    }

    @Test
    fun testDuplicateSmsEventHandling() {
        val testSms = "Monthly salary has been credited to your account."
        val res1 = classifier.classify(testSms)
        val res2 = classifier.classify(testSms)
        
        assertEquals(res1.classification, res2.classification)
        assertEquals(res1.confidencePercent, res2.confidencePercent)
        assertEquals(res1.probabilityScore, res2.probabilityScore, 0.001f)
    }
}
