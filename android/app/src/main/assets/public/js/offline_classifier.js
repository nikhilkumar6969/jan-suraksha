// Jan Suraksha - Offline In-Browser Scam Classifier
// Replicates the Android Kotlin OfflineSmsClassifier, TextNormalizer, and RuleGuardEngine.
// Uses exported weights in /content/scam_model_weights.json for 100% offline on-device inference.

const SurakshaOfflineClassifier = {
  isLoaded: false,
  loadPromise: null,
  intercept: 0.0,
  wordFeatures: new Map(), // key -> [idf, coef]
  charFeatures: new Map(), // key -> [idf, coef]

  // Hinglish phonetic standardisation matching TextNormalizer.kt
  HINGLISH_RULES: [
    [/\botpp?\b/gi, 'otp'],
    [/\bbijlee?\b/gi, 'bijli'],
    [/\bpulle?s\b/gi, 'police'],
    [/\bpulis\b/gi, 'police'],
    [/\bpaise?\b/gi, 'paisa'],
    [/\brupy?ee?\b/gi, 'rupaye'],
    [/\bgirafta+r\b/gi, 'arrest'],
    [/\bpa+rsa?l\b/gi, 'parcel'],
    [/\btura+nt\b/gi, 'immediately'],
    [/\ba\/c\b/gi, 'account'],
    [/\bacc\b/gi, 'account'],
    [/\byonoo?\b/gi, 'yono'],
    [/\banide+sk\b/gi, 'anydesk']
  ],

  // Safety & Threat Rules matching RuleGuardEngine.kt
  RULES: {
    GENUINE_SAFETY: [
      /(?:do\s+not|never)\s+share\s+(?:this\s+|your\s+)?(?:otp|code|pin|password)\b/i,
      /bank\s+never\s+(?:calls\s+to\s+)?asks?\s+(?:for\s+)?otp\b/i,
      /kisi\s+(?:ko|ke\s+saath)\s+share\s+na\s+kare[mn]?\b/i,
      /kisi\s+ko\s+na\s+bataye[mn]?\b/i,
      /साझा\s+न\s+करें/i,
      /किसी\s+को\s+न\s+बताएं/i,
      /ककरो\s+ले\s+झन\s+बताव/i,
      /ककरो\s+ले\s+(?:पिन\s+|पासवर्ड\s+)?साझा\s+झन\s+करव/i,
      /बैंक\s+कभी\s+भी\s+otp\s+नहीं\s+पूछता/i,
      /(?:college|university|school|institute).*(?:exam|semester|admit\s+card|portal|classes|syllabus)/i
    ],
    FRAUDULENT_OTP: [
      /(?:share|send|tell|give|enter|forward|put|type)\s+(?:the\s+)?(?:your\s+)?(?:google\s+pay\s+|gpay\s+|phonepe\s+|paytm\s+|bank\s+)?(?:6\s*[-]?\s*digit\s+)?(?:upi\s+)?(?:otp|pin|cvv|code|password)\b/i,
      /enter\s+(?:your\s+)?(?:upi\s+)?pin\s+to\s+(?:receive|accept|get|credit)\s+(?:money|cashback|payment|rupees)\b/i,
      /(?:upi\s+)?pin\s+(?:dalo|batao|share\s+kare|daraw|bataw)\b/i,
      /otp\s+(?:batao|bataiye|send\s+karo|share\s+kare|dijiye|forward|bataye)\b/i,
      /पैसे\s+पाने\s+के\s+लिए\s+(?:अपना\s+)?(?:upi\s+)?पिन\s*(?:डालें|दर्ज\s+करें|लगाएं)/i,
      /खाता\s+म\s+प[ईइ]सा\s+आही.*(?:upi\s+)?पिन/i,
      /प[ईइ]सा\s+पाए\s+बर.*(?:upi\s+)?पिन/i,
      /ओटीपी\s*(?:बताएं|दीजिए|भेजें|दर्ज\s+करें|बताव|डारव|भेजव)/i,
      /card\s+ka\s+cvv\s+aur\s+otp\b/i
    ],
    DIGITAL_ARREST: [
      /digital\s+arrest\b/i,
      /डिजिटल\s+अरेस्ट\b/i,
      /stay\s+on\s+(?:the\s+)?(?:video\s+)?call\b/i,
      /do\s+not\s+(?:disconnect|cut)\s+(?:this\s+)?call\b/i,
      /drugs\s+(?:and\s+passports?\s+)?in\s+(?:your\s+)?parcel\b/i,
      /clearance\s+bond|जमानत\s+राशि/i,
      /cbi\s+(?:crime\s+branch|cyber\s+crime\s+cell)\b/i
    ],
    FAKE_KYC_OR_DISCONNECTION: [
      /(?:account|a\/c|yono|sim|debit\s+card)\s+(?:is\s+)?(?:suspended|blocked|deactivated|closed|sealed)\b/i,
      /electricity\s+(?:power\s+)?will\s+be\s+disconnected\s+tonight\b/i,
      /bijli\s+kaat\s+di\s+jayegi\b/i,
      /बिजली\s*(?:बिल|पावर)?.*(?:काट\s+दी\s+जाएगी|काट\s+देबो|कट\s+जाएगा)/i,
      /cspdcl\s+electricity\s+officer\b/i,
      /update\s+(?:your\s+)?kyc\s+immediately\b/i,
      /केवाईसी\s*अपडेट\b/i
    ],
    SUSPICIOUS_LINKS: [
      /\b(?:bit\.ly|tinyurl\.com|is\.gd|cutt\.ly|t\.co)\/\S+/i,
      /\b\w+[-_](?:kyc|sbi|yono|cspdcl|police|customs)\.(?:top|vip|xyz|cc|site|live|online|in)\b/i,
      /\b[a-zA-Z0-9.-]+\.apk\b/i
    ]
  },

  async init(jsonPath = '/content/scam_model_weights.json') {
    if (this.isLoaded) return true;
    if (this.loadPromise) return this.loadPromise;

    this.loadPromise = (async () => {
      try {
        let json = null;
        // 1. Try Cache Storage first for instant offline startup
        if (window.caches) {
          const match = await window.caches.match(jsonPath);
          if (match) {
            json = await match.json();
          }
        }
        // 2. Fetch from network or HTTP cache
        if (!json) {
          const res = await fetch(jsonPath);
          if (!res.ok) throw new Error(`HTTP ${res.status} fetching ${jsonPath}`);
          json = await res.json();
        }

        this.intercept = json.intercept || 0.0;
        this.wordFeatures.clear();
        this.charFeatures.clear();

        const words = json.word_features || {};
        for (const [k, v] of Object.entries(words)) {
          this.wordFeatures.set(k, v);
        }

        const chars = json.char_features || {};
        for (const [k, v] of Object.entries(chars)) {
          this.charFeatures.set(k, v);
        }

        this.isLoaded = true;
        console.log(`[SurakshaOfflineClassifier] Loaded ${this.wordFeatures.size} word features, ${this.charFeatures.size} char features.`);
        return true;
      } catch (err) {
        console.warn('[SurakshaOfflineClassifier] Failed to load offline weights:', err);
        this.isLoaded = false;
        return false;
      }
    })();

    return this.loadPromise;
  },

  normalize(text) {
    if (!text || !text.trim()) return '';
    let norm = text.trim().normalize('NFC').toLowerCase();
    for (const [pattern, repl] of this.HINGLISH_RULES) {
      norm = norm.replace(pattern, repl);
    }
    return norm.replace(/\s+/g, ' ').trim();
  },

  extractWordNgrams(normalizedText) {
    // Unicode words matching \b\w+\b
    const words = normalizedText.match(/\b\w+\b/gu) || [];
    const counts = new Map();

    for (let i = 0; i < words.length; i++) {
      const w = words[i];
      counts.set(w, (counts.get(w) || 0) + 1);
      if (i < words.length - 1) {
        const bg = `${w} ${words[i + 1]}`;
        counts.set(bg, (counts.get(bg) || 0) + 1);
      }
    }
    return counts;
  },

  extractCharNgrams(normalizedText, minN = 2, maxN = 5) {
    const counts = new Map();
    const len = normalizedText.length;
    for (let n = minN; n <= maxN; n++) {
      if (len >= n) {
        for (let i = 0; i <= len - n; i++) {
          const sub = normalizedText.substring(i, i + n);
          counts.set(sub, (counts.get(sub) || 0) + 1);
        }
      }
    }
    return counts;
  },

  evaluateRules(normalizedText) {
    let isGenuineBankAlert = false;
    let isExplicitOtpDemand = false;
    let isDigitalArrest = false;
    let isFakeKycOrBillCut = false;
    let hasSuspiciousLink = false;
    const matchedRules = [];
    const triggerPhrases = [];

    // 1. Genuine safety patterns
    for (const p of this.RULES.GENUINE_SAFETY) {
      const m = normalizedText.match(p);
      if (m) {
        isGenuineBankAlert = true;
        matchedRules.push('GENUINE_BANK_GUARD');
        triggerPhrases.push(m[0]);
        break;
      }
    }

    // 2. Fraudulent OTP demands
    for (const p of this.RULES.FRAUDULENT_OTP) {
      const m = normalizedText.match(p);
      if (m) {
        const phrase = m[0].toLowerCase();
        if (!phrase.includes('न बताएं') && !phrase.includes('do not') && !phrase.includes('never') && !phrase.includes('झन')) {
          isExplicitOtpDemand = true;
          matchedRules.push('EXPLICIT_OTP_THEFT');
          triggerPhrases.push(m[0]);
          break;
        }
      }
    }

    // 3. Digital arrest threats
    for (const p of this.RULES.DIGITAL_ARREST) {
      const m = normalizedText.match(p);
      if (m) {
        isDigitalArrest = true;
        matchedRules.push('DIGITAL_ARREST_EXTORTION');
        triggerPhrases.push(m[0]);
        break;
      }
    }

    // 4. Fake KYC or Bill Cut
    for (const p of this.RULES.FAKE_KYC_OR_DISCONNECTION) {
      const m = normalizedText.match(p);
      if (m) {
        isFakeKycOrBillCut = true;
        matchedRules.push('URGENCY_EXTORTION');
        triggerPhrases.push(m[0]);
        break;
      }
    }

    // 5. Suspicious links
    for (const p of this.RULES.SUSPICIOUS_LINKS) {
      const m = normalizedText.match(p);
      if (m) {
        hasSuspiciousLink = true;
        matchedRules.push('PHISHING_LINK');
        triggerPhrases.push(m[0]);
        break;
      }
    }

    return {
      isGenuineBankAlert,
      isExplicitOtpDemand,
      isDigitalArrest,
      isFakeKycOrBillCut,
      hasSuspiciousLink,
      matchedRules,
      triggerPhrases
    };
  },

  classify(rawText, headerCheck = null) {
    if (!rawText || !rawText.trim()) {
      return {
        verdict: 'genuine',
        confidence_percent: 100,
        probability_scam: 0.0,
        explanation: 'Empty message text.',
        matched_rules: [],
        top_ngrams: [],
        highlighted_html: '',
        stages: { current_stage: 0, stages: [] },
        is_offline_model: true
      };
    }

    const normalized = this.normalize(rawText);
    const rules = this.evaluateRules(normalized);

    // ML Inference
    let mlProbSpam = 0.5;
    const contributingNgrams = [];

    if (this.isLoaded) {
      // Word Features
      const wordCounts = this.extractWordNgrams(normalized);
      let wNormSq = 0.0;
      let wDot = 0.0;

      for (const [term, cnt] of wordCounts.entries()) {
        const weights = this.wordFeatures.get(term);
        if (weights) {
          const idf = weights[0];
          const coef = weights[1];
          const tf = 1.0 + Math.log(cnt);
          const val = tf * idf;
          wNormSq += val * val;
          wDot += val * coef;

          if (coef > 0.05) {
            contributingNgrams.push({ ngram: term, weight: parseFloat(coef.toFixed(3)) });
          }
        }
      }
      const wScore = wNormSq > 0.0 ? (wDot / Math.sqrt(wNormSq)) : 0.0;

      // Char Features
      const charCounts = this.extractCharNgrams(normalized, 2, 5);
      let cNormSq = 0.0;
      let cDot = 0.0;

      for (const [term, cnt] of charCounts.entries()) {
        const weights = this.charFeatures.get(term);
        if (weights) {
          const idf = weights[0];
          const coef = weights[1];
          const tf = 1.0 + Math.log(cnt);
          const val = tf * idf;
          cNormSq += val * val;
          cDot += val * coef;
        }
      }
      const cScore = cNormSq > 0.0 ? (cDot / Math.sqrt(cNormSq)) : 0.0;

      const logit = wScore + cScore + this.intercept;
      mlProbSpam = 1.0 / (1.0 + Math.exp(-logit));
    }

    // Sort top contributing ngrams by weight descending
    contributingNgrams.sort((a, b) => b.weight - a.weight);
    const topNgrams = contributingNgrams.slice(0, 5);

    // Rule Overrides matching Kotlin OfflineSmsClassifier
    let finalVerdict = 'genuine';
    let finalScore = mlProbSpam;
    let explanation = '';
    let currentStage = 0;

    if (rules.isGenuineBankAlert && !rules.isExplicitOtpDemand) {
      finalVerdict = 'genuine';
      finalScore = 0.02;
      explanation = 'Authentic bank transaction/security alert with explicit "DO NOT SHARE" warning.';
      currentStage = 0;
    } else if (rules.isExplicitOtpDemand) {
      finalVerdict = 'likely_scam';
      finalScore = 0.98;
      explanation = 'High risk: Message attempts to solicit secret OTP or banking credentials.';
      currentStage = 3;
    } else if (rules.isDigitalArrest) {
      finalVerdict = 'likely_scam';
      finalScore = 0.98;
      explanation = 'Severe threat: Impersonating law enforcement with "Digital Arrest" extortion.';
      currentStage = 2;
    } else if (rules.isFakeKycOrBillCut) {
      finalVerdict = 'likely_scam';
      finalScore = rules.hasSuspiciousLink ? 0.98 : 0.94;
      explanation = 'Urgent power disconnection or account suspension threat detected.';
      currentStage = rules.hasSuspiciousLink ? 4 : 2;
    } else {
      if (mlProbSpam >= 0.50) {
        finalVerdict = 'likely_scam';
        finalScore = mlProbSpam;
        explanation = 'Classified as Scam by local on-device ML model.';
        currentStage = mlProbSpam > 0.85 ? 3 : 2;
      } else {
        finalVerdict = 'genuine';
        finalScore = mlProbSpam;
        explanation = 'No malicious patterns detected. Message appears genuine.';
        currentStage = 0;
      }
    }

    // Score fusion if TRAI sender header check is provided (0.45 header + 0.55 ML)
    if (headerCheck && typeof headerCheck.score === 'number') {
      const headerScamProb = headerCheck.is_fraud ? 0.95 : (headerCheck.is_official ? 0.05 : 0.50);
      finalScore = (0.45 * headerScamProb) + (0.55 * finalScore);
      if (finalScore >= 0.50) {
        finalVerdict = 'likely_scam';
      } else {
        finalVerdict = 'genuine';
      }
      explanation += ` [Fused TRAI Header Score: ${(finalScore * 100).toFixed(0)}%]`;
    }

    const confidence = finalVerdict === 'likely_scam'
      ? Math.round(finalScore * 100)
      : Math.round((1.0 - finalScore) * 100);

    // Build highlighted HTML with triggers and top ngrams
    let highlightedHtml = rawText;
    const highlightTerms = [...rules.triggerPhrases, ...topNgrams.map(t => t.ngram)];
    for (const term of highlightTerms) {
      if (term && term.length > 2) {
        try {
          const safeTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          const regex = new RegExp(`(${safeTerm})`, 'gi');
          highlightedHtml = highlightedHtml.replace(regex, '<mark class="scam-highlight">$1</mark>');
        } catch (e) {}
      }
    }

    return {
      verdict: finalVerdict,
      confidence_percent: Math.max(50, Math.min(100, confidence)),
      probability_scam: parseFloat(finalScore.toFixed(4)),
      explanation: explanation,
      matched_rules: rules.matchedRules,
      top_ngrams: topNgrams,
      highlighted_html: highlightedHtml,
      stages: {
        current_stage: currentStage,
        stages: ['Authority Claim', 'Urgency Panic', 'Sensitive Info', 'Malware/Payment']
      },
      is_offline_model: true
    };
  }
};

window.SurakshaOfflineClassifier = SurakshaOfflineClassifier;

// Auto-initialize when file loads in browser
if (typeof window !== 'undefined') {
  SurakshaOfflineClassifier.init();
}
