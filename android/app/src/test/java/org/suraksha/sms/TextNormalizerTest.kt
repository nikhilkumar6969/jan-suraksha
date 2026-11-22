package org.suraksha.sms

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.suraksha.sms.ml.TextNormalizer

class TextNormalizerTest {

    @Test
    fun testHinglishNormalization() {
        val raw = "Dear User, aapka bijlee bill pending hai. otpp share kare pulis se bache."
        val normalized = TextNormalizer.normalize(raw)
        
        assertTrue("Expected 'bijli' in normalized text", normalized.contains("bijli"))
        assertTrue("Expected 'otp' in normalized text", normalized.contains("otp"))
        assertTrue("Expected 'police' in normalized text", normalized.contains("police"))
    }

    @Test
    fun testWordNgramsExtraction() {
        val text = "electricity bill unpaid"
        val ngrams = TextNormalizer.extractWordNgrams(text)
        
        // Unigrams
        assertTrue(ngrams.containsKey("electricity"))
        assertTrue(ngrams.containsKey("bill"))
        assertTrue(ngrams.containsKey("unpaid"))
        
        // Bigrams
        assertTrue(ngrams.containsKey("electricity bill"))
        assertTrue(ngrams.containsKey("bill unpaid"))
    }

    @Test
    fun testCharNgramsExtraction() {
        val text = "otp"
        val charNgrams = TextNormalizer.extractCharNgrams(text, 2, 3)
        
        // 2-grams: ot, tp
        assertTrue(charNgrams.containsKey("ot"))
        assertTrue(charNgrams.containsKey("tp"))
        
        // 3-grams: otp
        assertTrue(charNgrams.containsKey("otp"))
    }

    @Test
    fun testEmptyAndWhitespaceInput() {
        val emptyResult = TextNormalizer.normalize("   ")
        assertEquals("", emptyResult)
        
        val emptyNgrams = TextNormalizer.extractWordNgrams("")
        assertTrue(emptyNgrams.isEmpty())
    }
}
