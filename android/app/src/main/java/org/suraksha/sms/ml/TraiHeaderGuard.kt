package org.suraksha.sms.ml

import android.content.Context
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.util.regex.Pattern
import kotlin.math.max
import kotlin.math.min

enum class HeaderRiskLevel {
    GREEN,
    AMBER,
    RED
}

data class ParsedSender(
    val raw: String,
    val isMobile: Boolean,
    val mobileNumber: String?,
    val operatorPrefix: String?,
    val cleanHeader: String,
    val suffix: String?,
    val isTraiFormat: Boolean
)

data class TraiHeaderResult(
    val score: Float, // 0.0 to 1.0 (1.0 = critical risk)
    val level: HeaderRiskLevel,
    val verdict: String, // "likely_scam", "unsure", "genuine"
    val matchedBrand: String?,
    val reasons: List<String>,
    val explanationHi: String,
    val explanationChg: String,
    val explanationEn: String,
    val parsedSender: ParsedSender
)

object TraiHeaderGuard {

    private val KNOWN_SHORTENERS = setOf(
        "bit.ly", "tinyurl.com", "is.gd", "cutt.ly", "t.co", "rb.gy", "shorturl.at"
    )

    private val FINANCIAL_KEYWORDS = listOf(
        Pattern.compile("\\b(?:bank|account|a/c|sbi|hdfc|icici|axis|pnb|bob|kotak|kyc|pan|aadhaar|debit|credit|atm|upi|pin|cashback|refund|subsidy|electricity|bill|disconnection|power|customs|parcel|arrest)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("(?:बैंक|खाता|केवाईसी|आधार|पैन|ओटीपी|पिन|पैसे|रुपये|बिजली|बिल|काट|बंद|फ्रीज|रिफंड|इनाम|चालान)", Pattern.CASE_INSENSITIVE),
        Pattern.compile("(?:पईसा|पइसा|तोर|तोला|कट जाही|कटही|पटाव|डारव|भेजव|बताव|झन|संझा|महतारी)", Pattern.CASE_INSENSITIVE)
    )

    private val URGENCY_KEYWORDS = listOf(
        Pattern.compile("\\b(?:urgent|immediately|today|now|expire|blocked|suspended)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("(?:तुरंत|अभी|आज\\s*रात|बंद\\s*हो\\s*जाएगा|काट\\s*दी\\s*जाएगी)", Pattern.CASE_INSENSITIVE)
    )

    private val APK_KEYWORDS = listOf(
        Pattern.compile("\\b[a-zA-Z0-9._-]+\\.apk\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\.apk\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(?:download\\s+app|install\\s+app|quicksupport|anydesk)\\b", Pattern.CASE_INSENSITIVE)
    )

    private val TRAI_REGEX = Pattern.compile("^([A-Za-z]{2})[-_]([A-Za-z0-9]{3,8})(?:[-_]([STPGstpg]))?$")
    private val URL_REGEX = Pattern.compile("(?:https?://)?(?:www\\.)?([a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})(?:/[^\\s]*)?", Pattern.CASE_INSENSITIVE)

    data class BrandEntry(
        val brand: String,
        val type: String,
        val headers: List<String>,
        val domains: List<String>
    )

    private var cachedBrands: List<BrandEntry>? = null

    @Synchronized
    fun loadRegistry(context: Context): List<BrandEntry> {
        cachedBrands?.let { return it }

        val list = mutableListOf<BrandEntry>()
        try {
            val inputStream = context.assets.open("headers.json")
            val reader = BufferedReader(InputStreamReader(inputStream, "UTF-8"))
            val sb = StringBuilder()
            var line: String?
            while (reader.readLine().also { line = it } != null) {
                sb.append(line)
            }
            reader.close()

            val root = JSONObject(sb.toString())
            val brandsArr = root.optJSONArray("brands")
            if (brandsArr != null) {
                for (i in 0 until brandsArr.length()) {
                    val bObj = brandsArr.getJSONObject(i)
                    val brandName = bObj.getString("brand")
                    val type = bObj.optString("type", "generic")

                    val hList = mutableListOf<String>()
                    val hArr = bObj.optJSONArray("headers")
                    if (hArr != null) {
                        for (j in 0 until hArr.length()) {
                            hList.add(hArr.getString(j).uppercase())
                        }
                    }

                    val dList = mutableListOf<String>()
                    val dArr = bObj.optJSONArray("domains")
                    if (dArr != null) {
                        for (j in 0 until dArr.length()) {
                            dList.add(dArr.getString(j).lowercase())
                        }
                    }

                    list.add(BrandEntry(brandName, type, hList, dList))
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }

        cachedBrands = list
        return list
    }

    fun parseSender(sender: String): ParsedSender {
        val clean = sender.trim()
        val digitsOnly = clean.replace(Regex("[^0-9]"), "")

        var normDigits = digitsOnly
        if (normDigits.startsWith("91") && normDigits.length == 12) {
            normDigits = normDigits.substring(2)
        } else if (normDigits.startsWith("0") && normDigits.length == 11) {
            normDigits = normDigits.substring(1)
        }

        if (normDigits.length == 10 && (normDigits.startsWith("6") || normDigits.startsWith("7") || normDigits.startsWith("8") || normDigits.startsWith("9"))) {
            return ParsedSender(clean, true, normDigits, null, normDigits, null, false)
        }

        val matcher = TRAI_REGEX.matcher(clean)
        if (matcher.matches()) {
            val prefix = matcher.group(1)?.uppercase()
            val header = matcher.group(2)?.uppercase() ?: ""
            val suffix = matcher.group(3)?.uppercase()
            return ParsedSender(clean, false, null, prefix, header, suffix, true)
        }

        val alphaOnly = clean.replace(Regex("[^A-Za-z0-9]"), "").uppercase()
        return ParsedSender(clean, false, null, null, alphaOnly, null, false)
    }

    fun checkSender(context: Context, sender: String, body: String): TraiHeaderResult {
        val brands = loadRegistry(context)
        val parsed = parseSender(sender)
        val bodyText = body.trim()

        val reasons = mutableListOf<String>()
        var score = 0.0f
        var matchedBrand: String? = null
        var matchedDomains = listOf<String>()

        val hasFinancial = FINANCIAL_KEYWORDS.any { it.matcher(bodyText).find() }
        val hasUrgency = URGENCY_KEYWORDS.any { it.matcher(bodyText).find() }
        val hasApk = APK_KEYWORDS.any { it.matcher(bodyText).find() }

        var hiReason = ""
        var chgReason = ""
        var enReason = ""

        // 1. Mobile number check
        if (parsed.isMobile) {
            if (hasFinancial) {
                score += 0.85f
                reasons.add("MOBILE_NUMBER_IMPERSONATION")
                hiReason = "यह संदेश व्यक्तिगत 10-अंकों के मोबाइल नंबर (+91-${parsed.mobileNumber}) से आया है जबकि इसमें बैंक/बिजली के दावे हैं। असली बैंक कभी मोबाइल नंबर से मैसेज नहीं करते।"
                chgReason = "ए संदेश 10 अंक के मोबाइल नंबर (+91-${parsed.mobileNumber}) ले आए हे। असली बैंक कभू साधारण मोबाइल नंबर ले मैसेज नइ भेजंय।"
                enReason = "SMS sent from personal 10-digit mobile (+91-${parsed.mobileNumber}) while claiming official banking/utility business."
            } else {
                score += 0.30f
                reasons.add("PERSONAL_MOBILE_SENDER")
                hiReason = "व्यक्तिगत मोबाइल नंबर (+91-${parsed.mobileNumber}) से संदेश आया है।"
                chgReason = "साधारण मोबाइल नंबर (+91-${parsed.mobileNumber}) ले संदेश आए हे।"
                enReason = "Message received from personal mobile (+91-${parsed.mobileNumber})."
            }
        }

        // 2. Header Registration & Lookalike Check
        val header = parsed.cleanHeader
        var exactMatch = false
        var lookalikeBrand: String? = null
        var lookalikeTarget: String? = null

        if (header.isNotEmpty() && !parsed.isMobile) {
            for (b in brands) {
                if (b.headers.contains(header)) {
                    exactMatch = true
                    matchedBrand = b.brand
                    matchedDomains = b.domains
                    break
                }
            }

            if (!exactMatch && header.length >= 4) {
                for (b in brands) {
                    for (regH in b.headers) {
                        val dist = computeLevenshtein(header, regH)
                        if (dist in 1..2) {
                            lookalikeBrand = b.brand
                            lookalikeTarget = regH
                            break
                        }
                    }
                    if (lookalikeBrand != null) break
                }
            }
        }

        if (lookalikeBrand != null && lookalikeTarget != null) {
            score += 0.90f
            reasons.add("LOOKALIKE_HEADER_TYPOSQUATTING")
            hiReason = "फर्जी हेडर अलर्ट! हेडर '$header' असली पंजीकृत हेडर '$lookalikeTarget' ($lookalikeBrand) की नकल है।"
            chgReason = "फर्जी हेडर खतरा! हेडर '$header' असली हेडर '$lookalikeTarget' के नकल आय।"
            enReason = "Header '$header' is a deceptive lookalike of registered header '$lookalikeTarget' ($lookalikeBrand)."
        }

        // 3. Domain validation
        val domainsInText = extractDomains(bodyText)
        var hasShortener = false
        var domainMismatch = false

        for (domain in domainsInText) {
            if (KNOWN_SHORTENERS.any { domain.endsWith(it) }) {
                hasShortener = true
                score += 0.40f
                reasons.add("URL_SHORTENER_DETECTED")
                if (hiReason.isEmpty()) {
                    hiReason = "संदेश में छुपा हुआ शॉर्ट लिंक ($domain) मिला है। असली बैंक शॉर्टलिंक नहीं भेजते।"
                    chgReason = "मैसेज म लुकाए होए शॉर्ट लिंक ($domain) हे। बैंक कभू शॉर्ट लिंक नइ भेजंय।"
                    enReason = "Concealed destination detected via link shortener ($domain)."
                }
            }

            if (exactMatch && matchedDomains.isNotEmpty()) {
                val matchesOfficial = matchedDomains.any { domain == it || domain.endsWith(".$it") }
                if (!matchesOfficial && !hasShortener) {
                    domainMismatch = true
                    score += 0.85f
                    reasons.add("BRAND_DOMAIN_MISMATCH")
                    hiReason = "फ़िशिंग लिंक का खतरा! हेडर $matchedBrand है परंतु लिंक बाहरी वेबसाइट ($domain) पर ले जा रहा है।"
                    chgReason = "फर्जी लिंक खतरा! हेडर $matchedBrand दिखत हे, फेर लिंक बाहरी साइट ($domain) के हे।"
                    enReason = "Phishing link detected: Sender claims to be $matchedBrand, but link points to unauthorized domain $domain."
                }
            }
        }

        if (hasUrgency) {
            score += 0.15f
            reasons.add("ARTIFICIAL_URGENCY")
        }

        if (hasApk) {
            score += 0.60f
            reasons.add("MALICIOUS_APK_DOWNLOAD")
            if (hiReason.isEmpty()) {
                hiReason = "संदेश में अज्ञात मोबाइल ऐप या APK फ़ाइल डाउनलोड करने को कहा गया है।"
                chgReason = "एसएमएस म ऐप या APK डाउनलोड करे बर कहे जात हे।"
                enReason = "Malicious App / APK download prompt detected in SMS."
            }
        }

        // Genuine OTP reward
        if (exactMatch && domainsInText.isEmpty() && !hasApk && !hasUrgency && lookalikeBrand == null) {
            val isCleanOtp = Pattern.compile("\\b(?:otp|code|verification|do not share|kisi ko na bataye|साझा न करें)\\b", Pattern.CASE_INSENSITIVE).matcher(bodyText).find()
            if (isCleanOtp) {
                score = max(0.0f, score - 0.40f)
                reasons.add("GENUINE_REGISTERED_HEADER")
                hiReason = "प्रमाणित हेडर: यह $matchedBrand का पंजीकृत सरकारी DLT हेडर है।"
                chgReason = "प्रमाणित हेडर: ए $matchedBrand के असली रजिस्टर्ड हेडर आय।"
                enReason = "Official registered TRAI DLT header verified for $matchedBrand."
            }
        }

        score = min(1.0f, max(0.0f, score))

        val level = when {
            score >= 0.70f -> HeaderRiskLevel.RED
            score >= 0.35f -> HeaderRiskLevel.AMBER
            else -> HeaderRiskLevel.GREEN
        }

        val verdict = when (level) {
            HeaderRiskLevel.RED -> "likely_scam"
            HeaderRiskLevel.AMBER -> "unsure"
            HeaderRiskLevel.GREEN -> "genuine"
        }

        if (hiReason.isEmpty()) {
            hiReason = when (level) {
                HeaderRiskLevel.RED -> "भारी खतरा! फर्जी हेडर या व्यक्तिगत मोबाइल नंबर से ठगी का प्रयास।"
                HeaderRiskLevel.AMBER -> "सावधान! अपंजीकृत हेडर या संदेहास्पद लिंक पहचाना गया।"
                HeaderRiskLevel.GREEN -> "सुरक्षित संदेश: ${matchedBrand ?: parsed.cleanHeader} के अधिकृत हेडर से सत्यापित।"
            }
        }
        if (chgReason.isEmpty()) {
            chgReason = when (level) {
                HeaderRiskLevel.RED -> "भारी खतरा! फर्जी हेडर या साधारण मोबाइल नंबर ले ठगी के संदेश आय।"
                HeaderRiskLevel.AMBER -> "सचेत रहव! संदेश म संदेहास्पद लिंक या हेडर दिखत हे।"
                HeaderRiskLevel.GREEN -> "सुरक्षित संदेश: ${matchedBrand ?: parsed.cleanHeader} के अधिकृत हेडर ले सत्यापित आय।"
            }
        }
        if (enReason.isEmpty()) {
            enReason = when (level) {
                HeaderRiskLevel.RED -> "Critical Risk: Suspicious or fraudulent SMS header detected."
                HeaderRiskLevel.AMBER -> "Caution: Unverified sender or suspicious cues detected."
                HeaderRiskLevel.GREEN -> "Verified Sender: Authentic message from ${matchedBrand ?: parsed.cleanHeader}."
            }
        }

        return TraiHeaderResult(
            score = score,
            level = level,
            verdict = verdict,
            matchedBrand = matchedBrand,
            reasons = reasons,
            explanationHi = hiReason,
            explanationChg = chgReason,
            explanationEn = enReason,
            parsedSender = parsed
        )
    }

    private fun extractDomains(text: String): List<String> {
        val list = mutableListOf<String>()
        val matcher = URL_REGEX.matcher(text)
        while (matcher.find()) {
            val domain = matcher.group(1)?.lowercase()
            if (domain != null) {
                list.add(domain)
            }
        }
        return list
    }

    private fun computeLevenshtein(s1: String, s2: String): Int {
        val dp = Array(s1.length + 1) { IntArray(s2.length + 1) }
        for (i in 0..s1.length) dp[i][0] = i
        for (j in 0..s2.length) dp[0][j] = j

        for (i in 1..s1.length) {
            for (j in 1..s2.length) {
                val cost = if (s1[i - 1] == s2[j - 1]) 0 else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    min(dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
                )
            }
        }
        return dp[s1.length][s2.length]
    }
}
