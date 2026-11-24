// Jan Suraksha - Offline Voice Intent Matcher (Multi-lingual: EN / HI / Hinglish / Chhattisgarhi)
// Deterministic keyword, n-gram & fuzzy phrase matching without cloud or heavy ML dependencies.

(function (global) {
  'use strict';

  const VoiceMatcher = {
    intentsData: null,

    // Embedded fallback dataset in case JSON fetch is deferred or in isolated unit tests
    defaultConfig: {
      substitutions: {
        "watsp": "whatsapp",
        "watsapp": "whatsapp",
        "watsap": "whatsapp",
        "whatsap": "whatsapp",
        "wtsp": "whatsapp",
        "vatsap": "whatsapp",
        "वॉटसप": "whatsapp",
        "व्हाट्सप": "whatsapp",
        "व्हाट्सऐप": "whatsapp",
        "व्हॉट्सएप": "whatsapp",
        "वाटसप": "whatsapp",
        "वॉट्सएप": "whatsapp",
        "meseg": "message",
        "massag": "message",
        "mesage": "message",
        "masage": "message",
        "smses": "sms",
        "msz": "message",
        "msg": "message",
        "fone": "phone",
        "fon": "phone",
        "kol": "call",
        "kall": "call",
        "pisa": "paisa",
        "pyasa": "paisa",
        "paise": "paisa",
        "rupya": "paisa",
        "rupaye": "paisa",
        "rupees": "paisa",
        "रुपिया": "paisa",
        "पइसा": "paisa",
        "पईसा": "paisa",
        "pulish": "police",
        "pulis": "police",
        "pulese": "police",
        "daroga": "police",
        "kotwali": "police",
        "cur": "qr",
        "qur": "qr",
        "kyuar": "qr",
        "kyu aar": "qr",
        "kew r": "qr"
      },
      fillerWords: new Set([
        "please", "bhai", "ji", "sir", "madam", "ek", "kripya", "zara",
        "hai", "tha", "hoga", "batao", "karo", "do", "de", "le", "ko",
        "se", "pe", "par", "mein", "me", "ka", "ki", "ke", "mor", "tola",
        "tor", "hawn", "ahe", "he", "ge", "aayis", "aaya", "aayi", "lag",
        "raha", "rahi", "gaya", "gayi", "kuch", "kisi", "mera", "meri", "mere",
        "apna", "apne", "hum", "mujhe", "mola", "hamein"
      ])
    },

    async init() {
      if (this.intentsData) return;
      try {
        const res = await fetch('/content/voice_intents.json');
        if (res.ok) {
          this.intentsData = await res.json();
        }
      } catch (err) {
        console.warn('[VoiceMatcher] Using embedded intent dataset fallback:', err);
      }
    },

    normalize(rawText) {
      if (!rawText || typeof rawText !== 'string') return '';
      let text = rawText.toLowerCase().trim();

      // Pre-normalize common multi-word speech artifacts
      text = text
        .replace(/\bkew\s+r\b/g, 'qr')
        .replace(/\bwhats\s+app\b/g, 'whatsapp')
        .replace(/\bkyu\s+aar\b/g, 'qr')
        .replace(/\bq\s+r\b/g, 'qr')
        .replace(/\b1930\b/g, '1930')
        .replace(/\b19\s*30\b/g, '1930');

      // Remove punctuation and special characters
      text = text.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?"'।]/g, ' ');

      // Split into tokens
      const rawTokens = text.split(/\s+/).filter(Boolean);
      const subs = (this.intentsData && this.intentsData.substitutions) || this.defaultConfig.substitutions;
      
      const normalizedTokens = rawTokens.map(tok => {
        // Do not substitute 'kal' unconditionally (in Hindi 'kal' means yesterday/tomorrow)
        if (tok === 'kal') return 'kal';
        return subs[tok] || tok;
      });
      return normalizedTokens.join(' ');
    },

    /**
     * Matches raw input transcript against the 5 core intents:
     * - whatsapp_or_sms_message
     * - phone_call
     * - qr_payment
     * - lost_money
     * - learn
     */
    match(rawText) {
      const clean = this.normalize(rawText);
      if (!clean) {
        return { intent: null, confidence: 0, raw: rawText };
      }

      const tokens = clean.split(' ');
      const tokenSet = new Set(tokens);

      const has = (w) => tokenSet.has(w) || clean.includes(w);

      // 1. Check direct phrase match against dataset
      const phrasesMatch = this.checkPhraseMatch(clean);
      if (phrasesMatch) {
        return phrasesMatch;
      }

      // 2. Deterministic keyword and weighted intent scoring
      const scores = {
        whatsapp_or_sms_message: 0,
        phone_call: 0,
        qr_payment: 0,
        lost_money: 0,
        learn: 0
      };

      // --- Intent: whatsapp_or_sms_message ---
      const isWa = has('whatsapp') || has('whats app') || has('watsap') || has('व्हाट्सएप') || has('व्हाट्सऐप') || has('वॉटसप');
      const isMsg = has('message') || has('sms') || has('मैसेज') || has('मेसेज') || has('संदेश') || has('text') || has('चिट्ठी');
      const isLink = has('link') || has('लिंक') || has('forward');

      if (isWa && (isMsg || isLink || has('aaya') || has('check') || has('आया') || has('आइस') || has('भेजे'))) {
        scores.whatsapp_or_sms_message += 12;
      } else if (isWa) {
        scores.whatsapp_or_sms_message += 8;
      }
      if (isMsg && (has('check') || has('aaya') || has('aaye') || has('aayis') || has('मिला') || has('आया') || has('आइस') || has('आए') || has('जांचव') || has('देखव'))) {
        scores.whatsapp_or_sms_message += 10;
      } else if (isMsg) {
        scores.whatsapp_or_sms_message += 6;
      }
      if (isLink && (has('message') || has('sms') || has('whatsapp') || has('पे') || has('म'))) {
        scores.whatsapp_or_sms_message += 6;
      }

      // --- Intent: phone_call ---
      const isCall = has('call') || has('कॉल') || has('phone') || has('फोन') || has('calling') || (has('kal') && (has('aaya') || has('kiya') || has('police') || has('thana')));
      const isPolice = has('police') || has('पुलिस') || has('cbi') || has('सीबीआई') || has('customs') || has('कस्टम') || has('thana') || has('थाना') || has('kotwali') || has('कोतवाली') || has('inspector') || has('officer');
      const isArrest = has('arrest') || has('अरेस्ट') || has('डिजिटल अरेस्ट') || has('digital arrest') || has('warrant') || has('वारंट') || has('dhamki') || has('धमकी');

      if (isCall && (isPolice || isArrest || has('aaya') || has('आया') || has('आइस') || has('kar raha') || has('check') || has('जांचव') || has('सुनव'))) {
        scores.phone_call += 12;
      } else if (isCall) {
        scores.phone_call += 6;
      }
      if (isPolice && isArrest) {
        scores.phone_call += 11;
      } else if (isPolice && isCall) {
        scores.phone_call += 10;
      }

      // --- Intent: qr_payment ---
      const isQr = has('qr') || has('क्यूआर') || has('barcode') || has('बारकोड') || has('scanner') || has('स्कैनर');
      const isScan = has('scan') || has('स्कैन') || has('स्कैनर');
      const isPayment = has('payment') || has('पेमेंट') || has('request') || has('रिक्वेस्ट') || has('paytm') || has('phonepe') || has('gpay') || has('upi') || has('यूपीआई');

      if (isQr && (isScan || isPayment || has('code') || has('कोड') || has('check') || has('जांचव'))) {
        scores.qr_payment += 12;
      } else if (isQr) {
        scores.qr_payment += 9;
      }
      if (isScan && (has('code') || isPayment || has('दुकान') || has('पईसा') || has('पैसा'))) {
        scores.qr_payment += 8;
      }

      // --- Intent: lost_money ---
      const isMoney = has('paisa') || has('paise') || has('पैसे') || has('पईसा') || has('रुपये') || has('balance') || has('savings');
      const isCut = has('kat') || has('kat gaya') || has('cut') || has('कट') || has('उड़') || has('udd') || has('chala gaya') || has('stolen') || has('chori') || has('लुट') || has('lut');
      const isFraud = has('fraud') || has('फ्रॉड') || has('thagi') || has('ठगी') || has('scam') || has('धोखा') || has('धोखाधड़ी') || has('1930') || has('helpline');

      if (isMoney && isCut) {
        scores.lost_money += 12;
      }
      if (isFraud && (isMoney || has('mere saath') || has('hoge') || has('ho gaya') || has('हो गया') || has('हो गे') || has('संग'))) {
        scores.lost_money += 12;
      }
      if (has('1930') || has('१९३०') || (has('helpline') && has('call'))) {
        scores.lost_money += 12;
      }
      if (isFraud && !isCall && !isMsg) {
        scores.lost_money += 7;
      }

      // --- Intent: learn ---
      const isTeach = has('teach') || has('learn') || has('सीखना') || has('सीखें') || has('सिखाओ') || has('सिखाव') || has('sikhao') || has('seekhna');
      const isLesson = has('lesson') || has('lessons') || has('पाठ') || has('क्विज') || has('quiz') || has('education') || has('rules') || has('नियम') || has('tips');

      if (isTeach && (isLesson || has('me') || has('मुझे') || has('मोला') || has('सुरक्षा') || has('safety') || has('scam'))) {
        scores.learn += 12;
      } else if (isTeach) {
        scores.learn += 7;
      }
      if (isLesson && (has('show') || has('dikhao') || has('दिखाओ') || has('दिखाव') || has('खेलना') || has('start') || has('पढ़ाव'))) {
        scores.learn += 10;
      } else if (isLesson) {
        scores.learn += 6;
      }

      // Find top winning intent
      let topIntent = null;
      let topScore = 0;

      for (const [intentKey, score] of Object.entries(scores)) {
        if (score > topScore) {
          topScore = score;
          topIntent = intentKey;
        }
      }

      // Minimum threshold required for intent match
      if (topScore >= 6) {
        const subType = (topIntent === 'whatsapp_or_sms_message')
          ? (isWa ? 'whatsapp' : (has('sms') || has('एसएमएस') ? 'sms' : 'message'))
          : null;

        const targetMap = {
          whatsapp_or_sms_message: { view: 'check', subtab: 'subtab-sms' },
          phone_call: { view: 'check', subtab: 'subtab-call' },
          qr_payment: { view: 'check', subtab: 'subtab-qr' },
          lost_money: { view: 'help', subtab: null },
          learn: { view: 'learn', subtab: null }
        };

        const target = targetMap[topIntent] || { view: 'home', subtab: null };

        return {
          intent: topIntent,
          subType: subType,
          confidence: Math.min(0.99, Number((0.55 + (topScore * 0.04)).toFixed(2))),
          score: topScore,
          targetView: target.view,
          targetSubtab: target.subtab,
          cleanText: clean,
          raw: rawText
        };
      }

      return {
        intent: null,
        confidence: 0,
        score: topScore,
        cleanText: clean,
        raw: rawText
      };
    },

    checkPhraseMatch(cleanText) {
      if (!this.intentsData || !this.intentsData.intents) return null;

      for (const [intentId, intentObj] of Object.entries(this.intentsData.intents)) {
        if (!intentObj.phrases) continue;
        for (const langList of Object.values(intentObj.phrases)) {
          for (const phrase of langList) {
            const normPhrase = this.normalize(phrase);
            if (cleanText === normPhrase || cleanText.includes(normPhrase) || normPhrase.includes(cleanText)) {
              const isWa = cleanText.includes('whatsapp') || cleanText.includes('व्हाट्सएप');
              const isSms = cleanText.includes('sms') || cleanText.includes('एसएमएस');
              return {
                intent: intentId,
                subType: intentId === 'whatsapp_or_sms_message' ? (isWa ? 'whatsapp' : (isSms ? 'sms' : 'message')) : null,
                confidence: 0.98,
                score: 15,
                matchedPhrase: phrase,
                targetView: intentObj.target_view,
                targetSubtab: intentObj.target_subtab,
                cleanText: cleanText
              };
            }
          }
        }
      }
      return null;
    }
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceMatcher;
  } else {
    global.VoiceMatcher = VoiceMatcher;
  }
})(typeof window !== 'undefined' ? window : globalThis);
