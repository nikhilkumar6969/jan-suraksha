package org.suraksha.sms.ml

import java.text.Normalizer
import java.util.Locale
import java.util.regex.Pattern

object TextNormalizer {

    private val HINGLISH_REPLACEMENTS = mapOf(
        Pattern.compile("\\botpp?\\b", Pattern.CASE_INSENSITIVE) to "otp",
        Pattern.compile("\\bbijlee?\\b", Pattern.CASE_INSENSITIVE) to "bijli",
        Pattern.compile("\\bpulle?s\\b", Pattern.CASE_INSENSITIVE) to "police",
        Pattern.compile("\\bpulis\\b", Pattern.CASE_INSENSITIVE) to "police",
        Pattern.compile("\\bpaise?\\b", Pattern.CASE_INSENSITIVE) to "paisa",
        Pattern.compile("\\brupy?ee?\\b", Pattern.CASE_INSENSITIVE) to "rupaye",
        Pattern.compile("\\bgirafta+r\\b", Pattern.CASE_INSENSITIVE) to "arrest",
        Pattern.compile("\\bpa+rsa?l\\b", Pattern.CASE_INSENSITIVE) to "parcel",
        Pattern.compile("\\btura+nt\\b", Pattern.CASE_INSENSITIVE) to "immediately",
        Pattern.compile("\\ba/c\\b", Pattern.CASE_INSENSITIVE) to "account",
        Pattern.compile("\\bacc\\b", Pattern.CASE_INSENSITIVE) to "account",
        Pattern.compile("\\byonoo?\\b", Pattern.CASE_INSENSITIVE) to "yono",
        Pattern.compile("\\banide+sk\\b", Pattern.CASE_INSENSITIVE) to "anydesk"
    )

    private val WORD_PATTERN = Pattern.compile("(?u)\\b\\w+\\b")

    fun normalize(text: String): String {
        if (text.isBlank()) return ""

        // Unicode NFC normalization
        var normalized = Normalizer.normalize(text.trim(), Normalizer.Form.NFC).lowercase(Locale.ROOT)

        // Hinglish phonetic standardisation
        for ((pattern, repl) in HINGLISH_REPLACEMENTS) {
            normalized = pattern.matcher(normalized).replaceAll(repl)
        }

        // Clean excess whitespace
        return normalized.replace("\\s+".toRegex(), " ").trim()
    }

    fun extractWordNgrams(normalizedText: String): Map<String, Int> {
        val matcher = WORD_PATTERN.matcher(normalizedText)
        val words = mutableListOf<String>()
        while (matcher.find()) {
            words.add(matcher.group())
        }

        val counts = mutableMapOf<String, Int>()
        // Unigrams
        for (w in words) {
            counts[w] = (counts[w] ?: 0) + 1
        }
        // Bigrams
        for (i in 0 until words.size - 1) {
            val bg = "${words[i]} ${words[i + 1]}"
            counts[bg] = (counts[bg] ?: 0) + 1
        }
        return counts
    }

    fun extractCharNgrams(normalizedText: String, minN: Int = 2, maxN: Int = 5): Map<String, Int> {
        val counts = mutableMapOf<String, Int>()
        val len = normalizedText.length
        for (n in minN..maxN) {
            if (len >= n) {
                for (i in 0..len - n) {
                    val sub = normalizedText.substring(i, i + n)
                    counts[sub] = (counts[sub] ?: 0) + 1
                }
            }
        }
        return counts
    }
}
