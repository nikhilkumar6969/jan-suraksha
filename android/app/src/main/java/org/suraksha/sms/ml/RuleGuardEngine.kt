package org.suraksha.sms.ml

import java.util.regex.Pattern

object RuleGuardEngine {

    // Genuine bank warning patterns (banks explicitly warning NOT to share)
    private val GENUINE_SAFETY_PATTERNS = listOf(
        Pattern.compile("do\\s+not\\s+share\\s+(?:this\\s+)?(?:otp|code|password)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("never\\s+share\\s+(?:your\\s+)?(?:otp|pin|password)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("bank\\s+never\\s+(?:calls\\s+to\\s+)?asks?\\s+(?:for\\s+)?otp\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("kisi\\s+(?:ko|ke\\s+saath)\\s+share\\s+na\\s+kare[mn]?\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("kisi\\s+ko\\s+na\\s+bataye[mn]?\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("साझा\\s+न\\s+करें", Pattern.CASE_INSENSITIVE),
        Pattern.compile("किसी\\s+को\\s+न\\s+बताएं", Pattern.CASE_INSENSITIVE),
        Pattern.compile("ककरो\\s+ले\\s+झन\\s+बताव", Pattern.CASE_INSENSITIVE)
    )

    // Fraudulent OTP & UPI PIN demands
    private val FRAUDULENT_OTP_PATTERNS = listOf(
        Pattern.compile("(?:share|send|tell|give|enter|forward|put|type)\\s+(?:the\\s+)?(?:your\\s+)?(?:google\\s+pay\\s+|gpay\\s+|phonepe\\s+|paytm\\s+|bank\\s+)?(?:6\\s*[-]?\\s*digit\\s+)?(?:upi\\s+)?(?:otp|pin|cvv|code|password)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("enter\\s+(?:your\\s+)?(?:upi\\s+)?pin\\s+to\\s+(?:receive|accept|get|credit)\\s+(?:money|cashback|payment|rupees)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("(?:upi\\s+)?pin\\s+(?:dalo|batao|share\\s+kare|daraw|bataw)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("otp\\s+(?:batao|bataiye|send\\s+karo|share\\s+kare|dijiye|forward|bataye)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("पैसे\\s+पाने\\s+के\\s+लिए\\s+(?:अपना\\s+)?(?:upi\\s+)?पिन\\s*(?:डालें|दर्ज\\s+करें|लगाएं)", Pattern.CASE_INSENSITIVE),
        Pattern.compile("खाता\\s+म\\s+प[ईइ]सा\\s+आही.*(?:upi\\s+)?पिन", Pattern.CASE_INSENSITIVE),
        Pattern.compile("प[ईइ]सा\\s+पाए\\s+बर.*(?:upi\\s+)?पिन", Pattern.CASE_INSENSITIVE),
        Pattern.compile("ओटीपी\\s*(?:बताएं|दीजिए|भेजें|दर्ज\\s+करें|बताव|डारव)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("card\\s+ka\\s+cvv\\s+aur\\s+otp\\b", Pattern.CASE_INSENSITIVE)
    )

    // Digital Arrest Threats
    private val DIGITAL_ARREST_PATTERNS = listOf(
        Pattern.compile("digital\\s+arrest\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("डिजिटल\\s+अरेस्ट\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("stay\\s+on\\s+(?:the\\s+)?(?:video\\s+)?call\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("do\\s+not\\s+(?:disconnect|cut)\\s+(?:this\\s+)?call\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("drugs\\s+(?:and\\s+passports?\\s+)?in\\s+(?:your\\s+)?parcel\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("clearance\\s+bond|जमानत\\s+राशि", Pattern.CASE_INSENSITIVE)
    )

    // Fake KYC & Disconnection Threats
    private val FAKE_KYC_PATTERNS = listOf(
        Pattern.compile("(?:account|a/c|yono|sim|debit\\s+card)\\s+(?:is\\s+)?(?:suspended|blocked|deactivated|closed|sealed)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("electricity\\s+(?:power\\s+)?will\\s+be\\s+disconnected\\s+tonight\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("bijli\\s+kaat\\s+di\\s+jayegi\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("बिजली\\s+काट\\s+दी\\s+जाएगी\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("cspdcl\\s+electricity\\s+officer\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("update\\s+(?:your\\s+)?kyc\\s+immediately\\b", Pattern.CASE_INSENSITIVE)
    )

    // Suspicious Shortlinks & Fake Domains
    private val SUSPICIOUS_LINK_PATTERNS = listOf(
        Pattern.compile("\\b(?:bit\\.ly|tinyurl\\.com|is\\.gd|cutt\\.ly|t\\.co)/\\S+", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b\\w+[-_](?:kyc|sbi|yono|cspdcl|police|customs)\\.(?:top|vip|xyz|cc|site|live|online|in)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b[a-zA-Z0-9.-]+\\.apk\\b", Pattern.CASE_INSENSITIVE)
    )

    data class RuleCheckResult(
        val isGenuineBankAlert: Boolean,
        val isExplicitOtpDemand: Boolean,
        val isDigitalArrest: Boolean,
        val isFakeKycOrBillCut: Boolean,
        val hasSuspiciousLink: Boolean,
        val matchedRules: List<String>
    )

    fun evaluate(normalizedText: String): RuleCheckResult {
        var isGenuineAlert = false
        var isOtpDemand = false
        var isDigitalArrest = false
        var isFakeKyc = false
        var hasSuspiciousLink = false
        val matched = mutableListOf<String>()

        for (p in GENUINE_SAFETY_PATTERNS) {
            if (p.matcher(normalizedText).find()) {
                isGenuineAlert = true
                matched.add("GENUINE_BANK_GUARD")
                break
            }
        }

        for (p in FRAUDULENT_OTP_PATTERNS) {
            val matcher = p.matcher(normalizedText)
            if (matcher.find()) {
                val matchedText = matcher.group().lowercase()
                if (!matchedText.contains("न बताएं") && !matchedText.contains("do not") && !matchedText.contains("never")) {
                    isOtpDemand = true
                    matched.add("EXPLICIT_OTP_THEFT")
                    break
                }
            }
        }

        for (p in DIGITAL_ARREST_PATTERNS) {
            if (p.matcher(normalizedText).find()) {
                isDigitalArrest = true
                matched.add("DIGITAL_ARREST_EXTORTION")
                break
            }
        }

        for (p in FAKE_KYC_PATTERNS) {
            if (p.matcher(normalizedText).find()) {
                isFakeKyc = true
                matched.add("FAKE_KYC_DISCONNECTION")
                break
            }
        }

        for (p in SUSPICIOUS_LINK_PATTERNS) {
            if (p.matcher(normalizedText).find()) {
                hasSuspiciousLink = true
                matched.add("SUSPICIOUS_PHISHING_LINK")
                break
            }
        }

        return RuleCheckResult(
            isGenuineBankAlert = isGenuineAlert,
            isExplicitOtpDemand = isOtpDemand,
            isDigitalArrest = isDigitalArrest,
            isFakeKycOrBillCut = isFakeKyc,
            hasSuspiciousLink = hasSuspiciousLink,
            matchedRules = matched
        )
    }
}
