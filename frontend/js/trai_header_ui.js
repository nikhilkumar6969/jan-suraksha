// 100% Offline Client-Side TRAI DLT Sender Header Inspector & Smishing Guard
// Works completely in-browser without internet, with backend API fallback

const TraiHeaderUI = {
  registry: null,

  testScenarios: {
    sbi_genuine: {
      sender: "VM-SBIINB-T",
      body: "Dear Customer, 482910 is your OTP for transaction of Rs. 4,500.00 at Amazon. Do NOT share this OTP with anyone including bank staff.",
      label: "1. SBI Genuine Transaction OTP"
    },
    sbi_mobile_fake: {
      sender: "+919876543210",
      body: "Dear SBI User, your YONO account is blocked today. Update PAN immediately to unblock: http://sbi-kyc-verify.top",
      label: "2. 10-Digit Mobile SBI KYC Scam"
    },
    hdfc_lookalike: {
      sender: "VM-HDFCBNK",
      body: "Alert! Your HDFC debit card has been disabled due to pending KYC update. Call customer care 9827011223 immediately.",
      label: "3. Lookalike Header (HDFCBNK vs HDFCBK)"
    },
    airtel_lookalike: {
      sender: "BZ-AIRTEL1",
      body: "Your Airtel SIM e-KYC is incomplete. Your outgoing calls will be stopped at 9:30 PM. Call verification officer immediately.",
      label: "4. Lookalike Header (AIRTEL1 vs AIRTEL)"
    },
    brand_domain_mismatch: {
      sender: "AX-HDFCBK",
      body: "Dear HDFC Customer, your reward points worth Rs 7,850 are expiring today. Redeem cash directly to your account at: http://hdfc-rewards-claim.xyz",
      label: "5. Brand-Domain Phishing (Spoofed Link)"
    },
    url_shortener: {
      sender: "VM-SBIINB",
      body: "Dear Customer, claim your instant pre-approved personal loan of Rs 5 Lakhs within 2 hours. Click https://bit.ly/sbi-quick-loan",
      label: "6. Bitly Link Shortener Hazard"
    },
    income_tax_fake: {
      sender: "+919123456789",
      body: "Income Tax Department: An outstanding tax refund of Rs 15,490 has been approved. Submit your bank account number now: http://incometax-refunds.online",
      label: "7. Income Tax Refund 10-Digit Scam"
    },
    india_post_detained: {
      sender: "+919826011122",
      body: "India Post Notice: Your parcel #IN98219 has been detained at customs hub due to wrong pincode. Pay Rs 25 redelivery charge: http://indiapost-update.site",
      label: "8. India Post Parcel Detained Scam"
    },
    cspdcl_electricity_scam: {
      sender: "+919827099881",
      body: "प्रिय उपभोक्ता, आपकी बिजली लाइन आज रात 9:30 बजे काट दी जाएगी क्योंकि बिल अपडेट नहीं हुआ है। तुरंत 9827099881 पर संपर्क करें।",
      label: "9. CSPDCL Bijli Line Cut Threat"
    },
    mahtari_vandan_scam: {
      sender: "+919755123456",
      body: "नमस्कार, महतारी वंदन योजना के 1000 रुपया तोर खाता म आए बर अटके हे। योजना राशि पाए बर तुरते 200 रुपया सत्यापन शुल्क जमा करव अउ अपन गुप्त ओटीपी बताव।",
      label: "10. CG Mahtari Vandan Fraud"
    },
    phonepe_cashback: {
      sender: "+919988776655",
      body: "Congratulations! You won Rs. 3,999 Scratch Card cashback on PhonePe. Click to accept money: http://phonepe-rewards.top/claim",
      label: "11. PhonePe Fake Cashback Hazard"
    },
    apk_download_fraud: {
      sender: "VM-SBIINB",
      body: "Dear Customer, update your YONO Banking App to mandatory 2026 security patch. Download official update file: http://yono-security.top/yono_patch.apk",
      label: "12. Malicious Banking APK Download"
    },
    genuine_axis: {
      sender: "AD-AXISBK-T",
      body: "Your Axis Bank credit card ending 9012 was charged Rs 1,299 at Netflix. If not done by you, SMS BLOCK to 5676782.",
      label: "13. Axis Bank Genuine Notification"
    },
    genuine_cspdcl: {
      sender: "VK-CSPDCL",
      body: "Dear Consumer, payment of Rs 1,420 for Consumer No 10029384 received with thanks on 23-11-2026. Visit cspdcl.co.in for e-receipt.",
      label: "14. CSPDCL Official Payment Receipt"
    },
    genuine_digilocker: {
      sender: "VM-DGLCKR",
      body: "DigiLocker: 719283 is your OTP to sign in to your DigiLocker account. OTP is confidential, do not share it with anyone.",
      label: "15. DigiLocker Official Login OTP"
    }
  },

  async init() {
    this.bindEvents();
    this.renderScenarioChips();
    await this.loadRegistry();
  },

  async loadRegistry() {
    try {
      const res = await fetch('/content/headers.json');
      if (res.ok) {
        this.registry = await res.json();
        return;
      }
    } catch (e) {
      console.debug('Failed to fetch /content/headers.json, using API endpoint', e);
    }

    try {
      const apiRes = await fetch('/api/detect/sms-headers-db');
      if (apiRes.ok) {
        this.registry = await apiRes.json();
      }
    } catch (err) {
      console.warn('Could not load headers database from server', err);
    }
  },

  bindEvents() {
    const btnCheck = document.getElementById('btnCheckTraiHeader');
    const btnClear = document.getElementById('btnClearTraiHeader');
    const btnPaste = document.getElementById('btnPasteTraiBody');
    const senderInput = document.getElementById('traiSenderInput');
    const bodyInput = document.getElementById('traiBodyInput');

    if (btnCheck) {
      btnCheck.addEventListener('click', () => this.analyzeHeader());
    }

    if (btnClear) {
      btnClear.addEventListener('click', () => this.clearInputs());
    }

    if (btnPaste && bodyInput) {
      btnPaste.addEventListener('click', async () => {
        try {
          const text = await navigator.clipboard.readText();
          if (text) {
            bodyInput.value = text;
            if (window.App) window.App.showToast('📋 क्लिपबोर्ड से पेस्ट किया गया');
          }
        } catch (e) {
          if (window.App) window.App.showToast('क्लिपबोर्ड परमिशन नहीं मिली');
        }
      });
    }

    // Auto check on Enter in sender input
    if (senderInput) {
      senderInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') this.analyzeHeader();
      });
    }

    // Battery Optimization Guide Modal Triggers
    const btnBatteryGuide = document.getElementById('btnBatteryGuide');
    const modalBattery = document.getElementById('modalBatteryGuide');
    const btnCloseBattery = document.getElementById('btnCloseBatteryGuide');

    if (btnBatteryGuide && modalBattery) {
      btnBatteryGuide.addEventListener('click', () => {
        modalBattery.style.display = 'flex';
      });
    }

    if (btnCloseBattery && modalBattery) {
      btnCloseBattery.addEventListener('click', () => {
        modalBattery.style.display = 'none';
      });
    }

    // Close on backdrop click
    if (modalBattery) {
      modalBattery.addEventListener('click', (e) => {
        if (e.target === modalBattery) modalBattery.style.display = 'none';
      });
    }
  },

  renderScenarioChips() {
    const container = document.getElementById('traiScenarioChips');
    if (!container) return;

    container.innerHTML = '';
    Object.keys(this.testScenarios).forEach((key) => {
      const item = this.testScenarios[key];
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'sample-chip';
      chip.textContent = item.label;
      chip.addEventListener('click', () => {
        const sInput = document.getElementById('traiSenderInput');
        const bInput = document.getElementById('traiBodyInput');
        if (sInput) sInput.value = item.sender;
        if (bInput) bInput.value = item.body;
        this.analyzeHeader();
      });
      container.appendChild(chip);
    });
  },

  clearInputs() {
    const sInput = document.getElementById('traiSenderInput');
    const bInput = document.getElementById('traiBodyInput');
    const resultBox = document.getElementById('traiResultBox');

    if (sInput) sInput.value = '';
    if (bInput) bInput.value = '';
    if (resultBox) resultBox.style.display = 'none';
  },

  parseSender(sender) {
    const clean = (sender || '').trim();
    const digitsOnly = clean.replace(/[^0-9]/g, '');

    let normDigits = digitsOnly;
    if (normDigits.startsWith('91') && normDigits.length === 12) {
      normDigits = normDigits.substring(2);
    } else if (normDigits.startsWith('0') && normDigits.length === 11) {
      normDigits = normDigits.substring(1);
    }

    if (normDigits.length === 10 && /^[6789]/.test(normDigits)) {
      return {
        raw: clean,
        isMobile: true,
        mobileNumber: normDigits,
        operatorPrefix: null,
        cleanHeader: normDigits,
        suffix: null,
        isTraiFormat: false
      };
    }

    const traiMatch = clean.match(/^([A-Za-z]{2})[-_]([A-Za-z0-9]{3,8})(?:[-_]([STPGstpg]))?$/);
    if (traiMatch) {
      return {
        raw: clean,
        isMobile: false,
        mobileNumber: null,
        operatorPrefix: traiMatch[1].toUpperCase(),
        cleanHeader: traiMatch[2].toUpperCase(),
        suffix: traiMatch[3] ? traiMatch[3].toUpperCase() : null,
        isTraiFormat: true
      };
    }

    const alphaOnly = clean.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
    return {
      raw: clean,
      isMobile: false,
      mobileNumber: null,
      operatorPrefix: null,
      cleanHeader: alphaOnly,
      suffix: null,
      isTraiFormat: false
    };
  },

  levenshtein(s1, s2) {
    if (s1.length < s2.length) return this.levenshtein(s2, s1);
    if (s2.length === 0) return s1.length;

    let previousRow = Array.from({ length: s2.length + 1 }, (_, i) => i);
    for (let i = 0; i < s1.length; i++) {
      let currentRow = [i + 1];
      for (let j = 0; j < s2.length; j++) {
        const cost = s1[i] === s2[j] ? 0 : 1;
        currentRow.push(Math.min(
          currentRow[j] + 1,
          previousRow[j + 1] + 1,
          previousRow[j] + cost
        ));
      }
      previousRow = currentRow;
    }
    return previousRow[s2.length];
  },

  async analyzeHeader() {
    const sInput = document.getElementById('traiSenderInput');
    const bInput = document.getElementById('traiBodyInput');
    const btnCheck = document.getElementById('btnCheckTraiHeader');

    const sender = (sInput ? sInput.value : '').trim();
    const body = (bInput ? bInput.value : '').trim();

    if (!sender && !body) {
      if (window.App) window.App.showToast('कृपया प्रेषक ID (Sender) या संदेश दर्ज करें');
      return;
    }

    if (btnCheck) {
      btnCheck.disabled = true;
      btnCheck.textContent = 'जांच हो रही है...';
    }

    const currentLang = (window.I18n && window.I18n.currentLang) || 'hi';

    try {
      // 1. Try local backend API for full fusion
      const res = await fetch('/api/detect/sms-header', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender: sender, body: body, language: currentLang })
      });

      if (res.ok) {
        const data = await res.json();
        this.renderResult(data.header_evaluation, data.content_evaluation, currentLang);
        return;
      }
    } catch (e) {
      console.debug('Backend offline, running local in-browser TRAI engine fallback', e);
    } finally {
      if (btnCheck) {
        btnCheck.disabled = false;
        btnCheck.textContent = 'हेडर व SMS परखें';
      }
    }

    // 2. Client-side fully offline fallback with 0.45 Header + 0.55 ML Score Fusion
    const localHeaderResult = this.clientSideCheck(sender, body, currentLang);
    let localContentResult = null;
    if (body && window.SurakshaOfflineClassifier) {
      if (!window.SurakshaOfflineClassifier.isLoaded) {
        await window.SurakshaOfflineClassifier.init();
      }
      localContentResult = window.SurakshaOfflineClassifier.classify(body);
      const headerScore = localHeaderResult.score;
      const mlScore = localContentResult.probability_scam;
      const fusedScore = (0.45 * headerScore) + (0.55 * mlScore);
      localHeaderResult.score = fusedScore;
      localHeaderResult.level = fusedScore >= 0.70 ? 'RED' : (fusedScore >= 0.35 ? 'AMBER' : 'GREEN');
      localHeaderResult.verdict = localHeaderResult.level === 'RED' ? 'likely_scam' : (localHeaderResult.level === 'AMBER' ? 'unsure' : 'genuine');
      localHeaderResult.explanation += ` [Fused Header+ML Score: ${(fusedScore * 100).toFixed(0)}%]`;
    }
    this.renderResult(localHeaderResult, localContentResult, currentLang);
  },

  clientSideCheck(sender, body, lang) {
    const parsed = this.parseSender(sender);
    const brands = (this.registry && this.registry.brands) || [];
    let score = 0.0;
    const reasons = [];

    const hasFinancial = /(?:bank|account|sbi|hdfc|icici|axis|pnb|bob|kotak|kyc|pan|aadhaar|debit|credit|atm|upi|pin|cashback|refund|subsidy|electricity|bill|disconnection|customs|parcel|arrest|पईसा|खाता|बैंक|केवाईसी|बिजली|चालान)/i.test(body);
    const hasUrgency = /(?:urgent|immediately|today|now|expire|blocked|suspended|तुरंत|अभी|आज\s*रात|बंद)/i.test(body);
    const hasApk = /\.apk\b|download\s+app|install\s+app|anydesk|quicksupport/i.test(body);

    let matchedBrand = null;
    let matchedDomains = [];

    if (parsed.isMobile) {
      if (hasFinancial) {
        score += 0.85;
        reasons.push({
          rule: 'MOBILE_NUMBER_IMPERSONATION',
          severity: 'CRITICAL',
          en: `SMS sent from personal 10-digit mobile (+91-${parsed.mobileNumber}) claiming banking/utility business.`,
          hi: `यह संदेश व्यक्तिगत 10-अंकों के मोबाइल नंबर (+91-${parsed.mobileNumber}) से आया है जबकि इसमें बैंक/बिजली के दावे हैं। असली बैंक कभी मोबाइल नंबर से मैसेज नहीं करते।`,
          chg: `ए संदेश 10 अंक के मोबाइल नंबर (+91-${parsed.mobileNumber}) ले आए हे। असली बैंक कभू साधारण मोबाइल नंबर ले मैसेज नइ भेजंय।`
        });
      } else {
        score += 0.30;
        reasons.push({
          rule: 'PERSONAL_MOBILE_SENDER',
          severity: 'LOW',
          en: `Message received from personal mobile (+91-${parsed.mobileNumber}).`,
          hi: `व्यक्तिगत मोबाइल नंबर (+91-${parsed.mobileNumber}) से संदेश प्राप्त हुआ।`,
          chg: `साधारण मोबाइल नंबर (+91-${parsed.mobileNumber}) ले संदेश आए हे।`
        });
      }
    }

    const header = parsed.cleanHeader;
    let exactMatch = false;
    let lookalikeFound = null;

    if (header && !parsed.isMobile) {
      for (const b of brands) {
        if (b.headers && b.headers.map((h) => h.toUpperCase()).includes(header)) {
          exactMatch = true;
          matchedBrand = b.brand;
          matchedDomains = (b.domains || []).map((d) => d.toLowerCase());
          break;
        }
      }

      if (!exactMatch && header.length >= 4) {
        for (const b of brands) {
          for (const regH of b.headers || []) {
            const dist = this.levenshtein(header, regH.toUpperCase());
            if (dist >= 1 && dist <= 2) {
              lookalikeFound = {
                input: header,
                genuine: regH.toUpperCase(),
                brand: b.brand,
                distance: dist
              };
              break;
            }
          }
          if (lookalikeFound) break;
        }
      }
    }

    if (lookalikeFound) {
      score += 0.90;
      reasons.push({
        rule: 'LOOKALIKE_HEADER_TYPOSQUATTING',
        severity: 'CRITICAL',
        en: `Header '${lookalikeFound.input}' is a deceptive lookalike of registered header '${lookalikeFound.genuine}' (${lookalikeFound.brand}).`,
        hi: `फर्जी हेडर अलर्ट! हेडर '${lookalikeFound.input}' असली पंजीकृत हेडर '${lookalikeFound.genuine}' (${lookalikeFound.brand}) की नकल है।`,
        chg: `फर्जी हेडर खतरा! हेडर '${lookalikeFound.input}' असली हेडर '${lookalikeFound.genuine}' के नकल आय।`
      });
    }

    // Domain check
    const urlMatches = body.match(/(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/gi) || [];
    const shorteners = ['bit.ly', 'tinyurl.com', 'is.gd', 'cutt.ly', 't.co', 'rb.gy'];

    for (const rawUrl of urlMatches) {
      const cleanUrl = rawUrl.toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
      if (shorteners.some((s) => cleanUrl.endsWith(s))) {
        score += 0.40;
        reasons.push({
          rule: 'URL_SHORTENER_DETECTED',
          severity: 'HIGH',
          en: `Hidden destination detected via shortlink (${cleanUrl}). Banks do not use public shortlinks for official alerts.`,
          hi: `संदेश में छुपा हुआ शॉर्ट लिंक (${cleanUrl}) मिला है। असली बैंक महत्वपूर्ण सूचनाओं के लिए शॉर्टलिंक नहीं भेजते।`,
          chg: `मैसेज म लुकाए होए शॉर्ट लिंक (${cleanUrl}) हे। बैंक कभू शॉर्ट लिंक नइ भेजंय।`
        });
      }

      if (exactMatch && matchedDomains.length > 0) {
        const matchesOfficial = matchedDomains.some((d) => cleanUrl === d || cleanUrl.endsWith('.' + d));
        if (!matchesOfficial) {
          score += 0.85;
          reasons.push({
            rule: 'BRAND_DOMAIN_MISMATCH',
            severity: 'CRITICAL',
            en: `Phishing link: Sender claims to be ${matchedBrand}, but enclosed link points to ${cleanUrl} instead of ${matchedDomains[0]}.`,
            hi: `फ़िशिंग लिंक का खतरा! प्रेषक ${matchedBrand} है, परंतु लिंक किसी बाहरी वेबसाइट (${cleanUrl}) पर ले जा रहा है।`,
            chg: `फर्जी लिंक खतरा! हेडर ${matchedBrand} दिखत हे, फेर लिंक बाहरी साइट (${cleanUrl}) के हे।`
          });
        }
      }
    }

    if (hasUrgency) {
      score += 0.15;
      reasons.push({
        rule: 'ARTIFICIAL_URGENCY',
        severity: 'MEDIUM',
        en: 'Panic tactics detected (threats of disconnection or account block).',
        hi: 'घबराहट पैदा करने वाले शब्द (तुरंत खाता बंद होने या बिजली कटने की धमकी)।',
        chg: 'डरवाए बर तुरंत खाता बंद करे या बिजली काटे के धमकी देहे जात हे।'
      });
    }

    if (hasApk) {
      score += 0.60;
      reasons.push({
        rule: 'MALICIOUS_APK_DOWNLOAD',
        severity: 'CRITICAL',
        en: 'App / APK download prompt in message. Banks NEVER distribute APK files via SMS.',
        hi: 'संदेश में अज्ञात मोबाइल ऐप या APK फ़ाइल डाउनलोड करने को कहा गया है।',
        chg: 'एसएमएस म ऐप या APK डाउनलोड करे बर कहे जात हे।'
      });
    }

    if (exactMatch && urlMatches.length === 0 && !hasApk && !hasUrgency && !lookalikeFound) {
      if (/(?:otp|code|verification|do not share|साझा न करें)/i.test(body)) {
        score = Math.max(0.0, score - 0.40);
        reasons.push({
          rule: 'GENUINE_REGISTERED_HEADER',
          severity: 'SAFE',
          en: `Official registered TRAI DLT header verified for ${matchedBrand}. No suspicious links found.`,
          hi: `प्रमाणित हेडर: यह ${matchedBrand} का पंजीकृत सरकारी DLT हेडर है। कोई संदेहास्पद लिंक नहीं है।`,
          chg: `प्रमाणित हेडर: ए ${matchedBrand} के असली रजिस्टर्ड हेडर आय।`
        });
      }
    }

    score = Math.min(1.0, Math.max(0.0, score));
    const level = score >= 0.70 ? 'RED' : (score >= 0.35 ? 'AMBER' : 'GREEN');
    const verdict = level === 'RED' ? 'likely_scam' : (level === 'AMBER' ? 'unsure' : 'genuine');

    let explanation = '';
    const topReason = reasons.find((r) => r.severity === 'CRITICAL') || reasons.find((r) => r.severity === 'HIGH') || reasons[0];
    if (topReason && topReason[lang]) {
      explanation = topReason[lang];
    } else {
      if (level === 'RED') explanation = lang === 'en' ? 'Critical Risk: Suspicious or fraudulent SMS header detected.' : 'भारी खतरा! फर्जी हेडर या व्यक्तिगत नंबर से ठगी का प्रयास।';
      else if (level === 'AMBER') explanation = lang === 'en' ? 'Caution: Unverified sender or urgency detected.' : 'सावधान! अपंजीकृत हेडर या संदेहास्पद लिंक पहचाना गया।';
      else explanation = lang === 'en' ? `Verified Sender: Authentic message from ${matchedBrand || parsed.cleanHeader}.` : `सुरक्षित संदेश: ${matchedBrand || parsed.cleanHeader} के अधिकृत हेडर से सत्यापित।`;
    }

    return {
      score: score,
      level: level,
      verdict: verdict,
      matched_brand: matchedBrand,
      reasons: reasons,
      header_info: parsed,
      explanation: explanation
    };
  },

  renderResult(headerEval, contentEval, lang) {
    const box = document.getElementById('traiResultBox');
    if (!box) return;

    const level = headerEval.level || 'AMBER';
    const isRed = level === 'RED';
    const isGreen = level === 'GREEN';

    box.className = `verdict-box show ${isRed ? 'danger' : (isGreen ? 'safe' : 'warning')}`;

    const parsed = headerEval.header_info || {};
    const brandName = headerEval.matched_brand || (parsed.isMobile ? `Personal Mobile (+91-${parsed.mobileNumber})` : 'Unregistered / Unknown Sender');

    // Operator breakdown tag
    let operatorBadge = '';
    if (parsed.operatorPrefix) {
      const opNames = {
        'AX': 'Airtel (AX)',
        'VM': 'Vi / Vodafone Idea (VM)',
        'BZ': 'BSNL (BZ)',
        'VK': 'Vi / Vodafone Idea (VK)',
        'AD': 'Airtel Delhi/West (AD)',
        'JD': 'Jio Delhi (JD)',
        'JZ': 'Jio (JZ)'
      };
      const opLabel = opNames[parsed.operatorPrefix] || `Operator Circle (${parsed.operatorPrefix})`;
      operatorBadge = `<span class="badge" style="background:#e0e7ff; color:#3730a3; margin-right:6px;">📡 ${opLabel}</span>`;
    }

    let statusPill = '';
    if (isRed) {
      statusPill = `<span class="badge badge-danger">🔴 उच्च जोखिम (HIGH RISK / RED)</span>`;
    } else if (isGreen) {
      statusPill = `<span class="badge badge-success">🟢 सुरक्षित प्रेषक (VERIFIED / GREEN)</span>`;
    } else {
      statusPill = `<span class="badge badge-warning">🟡 सतर्कता आवश्यक (CAUTION / AMBER)</span>`;
    }

    // Reasons HTML
    let reasonsHtml = '';
    if (headerEval.reasons && headerEval.reasons.length > 0) {
      reasonsHtml = `
        <div style="margin-top: var(--space-3); background: rgba(0,0,0,0.03); border-radius: 6px; padding: var(--space-3);">
          <div style="font-weight: 700; font-size: var(--text-sm); margin-bottom: 6px;">पहचाने गए मुख्य बिंदु (Findings):</div>
          <ul style="margin: 0; padding-left: 20px; font-size: var(--text-sm); line-height: 1.5;">
            ${headerEval.reasons.map((r) => `<li><strong>${r.rule || ''}</strong>: ${r[lang] || r.hi || r.en || ''}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    box.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2); flex-wrap: wrap; gap: 8px;">
        <div style="font-size: var(--text-lg); font-weight: 800;">
          ${isRed ? '🚨 धोखाधड़ी की चेतावनी (Smishing Alert)' : (isGreen ? '✅ प्रमाणित व सुरक्षित संदेश' : '⚠️ संदेहास्पद संदेश (Unverified)')}
        </div>
        <div>${statusPill}</div>
      </div>

      <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: var(--space-3);">
        <span class="badge" style="background:#f1f5f9; color:#0f172a; font-weight:700;">🏷️ हेडर: ${parsed.raw || parsed.cleanHeader || 'N/A'}</span>
        ${operatorBadge}
        <span class="badge" style="background:#ecfdf5; color:#065f46;">🏢 संस्था: ${brandName}</span>
        <span class="badge" style="background:#fef2f2; color:#991b1b;">📊 रिस्क स्कोर: ${Math.round((headerEval.score || 0) * 100)}%</span>
      </div>

      <div style="font-size: var(--text-base); font-weight: 600; line-height: 1.6; margin-bottom: var(--space-2);">
        ${headerEval.explanation || ''}
      </div>

      ${reasonsHtml}

      <div style="display: flex; gap: var(--space-3); margin-top: var(--space-4); flex-wrap: wrap;">
        <a href="tel:1930" class="btn btn-danger" style="text-decoration:none; display:inline-flex; align-items:center; gap:6px;">
          📞 1930 राष्ट्रीय हेल्पलाइन
        </a>
        <button type="button" class="btn btn-secondary" id="btnShareTraiAlert" style="display:inline-flex; align-items:center; gap:6px;">
          👨‍👩‍👧 परिवार को सचेत करें
        </button>
      </div>
    `;

    box.style.display = 'block';
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    const btnShare = document.getElementById('btnShareTraiAlert');
    if (btnShare) {
      btnShare.addEventListener('click', () => {
        const shareText = `⚠️ साइबर सतर्कता अलर्ट!\nमुझे इस हेडर/नंबर (${parsed.raw || 'Unknown'}) से संदेहास्पद SMS मिला है: "${headerEval.explanation}"।\nकृपया किसी भी लिंक पर क्लिक न करें। जन सुरक्षा ऐप।`;
        if (navigator.share) {
          navigator.share({ title: 'साइबर फ्रॉड अलर्ट', text: shareText }).catch(() => {});
        } else if (navigator.clipboard) {
          navigator.clipboard.writeText(shareText).then(() => {
            if (window.App) window.App.showToast('📋 चेतावनी संदेश कॉपी हो गया');
          });
        }
      });
    }
  }
};

window.TraiHeaderUI = TraiHeaderUI;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => TraiHeaderUI.init());
} else {
  TraiHeaderUI.init();
}
