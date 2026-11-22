package org.suraksha.sms

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.suraksha.sms.ml.RuleGuardEngine
import org.suraksha.sms.ml.TextNormalizer

class RuleGuardTest {

    @Test
    fun testGenuineBankOtpGuard() {
        val genuineSms = "582910 is your secret OTP for Rs 450 at Amazon. DO NOT SHARE WITH ANYONE. Bank never calls to ask OTP."
        val normalized = TextNormalizer.normalize(genuineSms)
        val result = RuleGuardEngine.evaluate(normalized)

        assertTrue("Expected genuine bank alert detected", result.isGenuineBankAlert)
        assertFalse("Expected no fraudulent OTP demand", result.isExplicitOtpDemand)
    }

    @Test
    fun testExplicitOtpTheftDetection() {
        val scamSms = "Your card is blocked. Share your 6 digit OTP with manager to unblock immediately."
        val normalized = TextNormalizer.normalize(scamSms)
        val result = RuleGuardEngine.evaluate(normalized)

        assertTrue("Expected explicit OTP demand detected", result.isExplicitOtpDemand)
    }

    @Test
    fun testDigitalArrestDetection() {
        val arrestSms = "Mumbai Crime Branch: Drugs parcel seized under your Aadhaar. You are under DIGITAL ARREST. Do not disconnect."
        val normalized = TextNormalizer.normalize(arrestSms)
        val result = RuleGuardEngine.evaluate(normalized)

        assertTrue("Expected digital arrest threat detected", result.isDigitalArrest)
    }

    @Test
    fun testElectricityDisconnectionThreat() {
        val billSms = "URGENT: CSPDCL notice. Your power will be disconnected tonight at 9:30 PM due to unpaid bill. Call 9876543210."
        val normalized = TextNormalizer.normalize(billSms)
        val result = RuleGuardEngine.evaluate(normalized)

        assertTrue("Expected fake KYC / bill cut threat detected", result.isFakeKycOrBillCut)
    }
}
