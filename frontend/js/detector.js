// Suraksha SMS / Message Scam Detector Frontend
const MessageDetector = {
  samples: {
    electricity: "URGENT: CSPDCL Electricity officer notice. Your electricity power will be disconnected tonight at 9:30 PM due to unpaid bill of Rs 1,450. Call officer at 9876543210 immediately.",
    digital_arrest: "CBI Crime Branch Notice: A parcel containing contraband drugs and fake passports registered to your Aadhaar was seized at Mumbai airport. You are in DIGITAL ARREST. Do not disconnect this call or tell anyone. Pay clearance bond of Rs 50000.",
    kyc_block: "Dear customer, your SBI account is suspended due to incomplete KYC. Update immediately at bit.ly/sbi-kyc-verify or account will be permanently blocked in 2 hours.",
    genuine_bank: "582910 is your secret OTP for transaction of Rs 450.00 at Flipkart. DO NOT SHARE WITH ANYONE. Bank never calls to ask OTP.",
    lottery: "Badhai ho! Aapka number KBC lottery me select hua hai rs 2500000 ke liye. Prize lene ke liye 6 digit OTP manager 9826102938 ko turant bataye."
  },

  init() {
    const btnAnalyze = document.getElementById('btnAnalyzeSms');
    const btnClear = document.getElementById('btnClearSms');
    const btnRead = document.getElementById('btnSmsReadAloud');
    const smsInput = document.getElementById('smsInput');

    if (btnAnalyze) {
      btnAnalyze.addEventListener('click', () => this.analyzeMessage());
    }
    if (btnClear) {
      btnClear.addEventListener('click', () => {
        if (smsInput) smsInput.value = '';
        const vBox = document.getElementById('smsVerdictBox');
        if (vBox) vBox.classList.remove('show', 'danger', 'warning', 'safe');
      });
    }
    if (btnRead) {
      btnRead.addEventListener('click', () => this.readAloud());
    }

    // Sample chips
    document.querySelectorAll('.sample-chip[data-sample]').forEach((chip) => {
      chip.addEventListener('click', () => {
        const key = chip.getAttribute('data-sample');
        if (this.samples[key] && smsInput) {
          smsInput.value = this.samples[key];
          this.analyzeMessage();
        }
      });
    });

    // Report and Help buttons inside verdict
    const btnReport = document.getElementById('btnReportFromVerdict');
    if (btnReport) {
      btnReport.addEventListener('click', () => {
        if (window.ReportsManager) {
          window.ReportsManager.openModal(smsInput ? smsInput.value : '');
        }
      });
    }

    const btnHelp = document.getElementById('btnHelpFromVerdict');
    if (btnHelp) {
      btnHelp.addEventListener('click', () => {
        if (window.App) window.App.navigate('help');
      });
    }
  },

  async analyzeMessage() {
    const input = document.getElementById('smsInput');
    if (!input || !input.value.trim()) {
      if (window.App) window.App.showToast('कृपया पहले संदेश यहाँ पेस्ट करें (Please enter message)');
      return;
    }

    const text = input.value.trim();
    const lang = I18n.currentLang || 'hi';

    try {
      const res = await fetch('/api/detect/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language: lang })
      });

      if (!res.ok) throw new Error('Backend check failed');
      const data = await res.json();
      this.renderVerdict(data);
    } catch (err) {
      console.warn('Network error, using offline heuristic detection:', err);
      // Client-side offline fallback
      this.renderOfflineFallback(text);
    }
  },

  renderVerdict(data) {
    const box = document.getElementById('smsVerdictBox');
    const vTitle = document.getElementById('verdictTitle');
    const vConf = document.getElementById('verdictConfidence');
    const vExpl = document.getElementById('verdictExplanation');
    const vHigh = document.getElementById('smsHighlightedText');
    const vIcon = document.getElementById('verdictIcon');
    const vNgrams = document.getElementById('ngramTokensBox');

    if (!box) return;

    box.classList.remove('danger', 'warning', 'safe');

    if (data.verdict === 'likely_scam') {
      box.classList.add('danger');
      vTitle.textContent = I18n.t('verdict_likely_scam', 'Likely Scam (खतरा / High Risk)');
      vIcon.innerHTML = `<svg viewBox="0 0 24 24"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>`;
    } else if (data.verdict === 'unsure') {
      box.classList.add('warning');
      vTitle.textContent = I18n.t('verdict_unsure', 'Unsure (संदेहास्पद / Verify with Bank)');
      vIcon.innerHTML = `<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 16h-2v-2h2v2zm1.07-7.75l-.9.92C12.45 11.9 12 12.5 12 14h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H7c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.04-.42 1.99-1.07 2.75z"/></svg>`;
    } else {
      box.classList.add('safe');
      vTitle.textContent = I18n.t('verdict_genuine', 'Looks Genuine (सामान्य / Safe)');
      vIcon.innerHTML = `<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>`;
    }

    vConf.textContent = `Confidence Score: ${data.confidence_percent}%`;
    vExpl.textContent = data.explanation;
    vHigh.innerHTML = data.highlighted_html || '';

    // Stage progression timeline
    const stages = data.stages ? data.stages.stages : [];
    const maxStage = data.stages ? data.stages.current_stage : 0;
    for (let s = 1; s <= 4; s++) {
      const stepEl = document.getElementById(`stageStep${s}`);
      if (stepEl) {
        if (s <= maxStage) {
          stepEl.classList.add('active');
        } else {
          stepEl.classList.remove('active');
        }
      }
    }

    // Model contributing ngrams
    if (vNgrams && data.top_ngrams && data.top_ngrams.length > 0) {
      const tags = data.top_ngrams.map(n => `<span style="background:var(--bg-card-subtle); border:1px solid var(--border-color); padding:2px 6px; border-radius:4px; margin-right:4px;">${n.ngram} (+${n.weight})</span>`).join('');
      vNgrams.innerHTML = `<strong>Model Contributing N-grams:</strong> ${tags}`;
    } else if (vNgrams) {
      vNgrams.innerHTML = '';
    }

    box.classList.add('show');
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  },

  renderOfflineFallback(text) {
    const textLower = text.toLowerCase();
    const isScam = textLower.includes('otp') || textLower.includes('kyc') || textLower.includes('arrest') || textLower.includes('bijli');
    this.renderVerdict({
      verdict: isScam ? 'likely_scam' : 'genuine',
      confidence_percent: 88,
      explanation: isScam ? 'Offline check detected keywords associated with high cyber fraud risks.' : 'No urgent fraud patterns detected offline.',
      highlighted_html: text,
      stages: { current_stage: isScam ? 2 : 0, stages: [] },
      top_ngrams: []
    });
  },

  readAloud() {
    const expl = document.getElementById('verdictExplanation');
    if (!expl || !window.speechSynthesis) return;

    const utterance = new SpeechSynthesisUtterance(expl.textContent);
    utterance.lang = (I18n.currentLang === 'en') ? 'en-IN' : 'hi-IN';
    utterance.rate = 0.9;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    if (window.App) window.App.showToast('🔊 बोलकर सुनाया जा रहा है (Playing audio)');
  }
};
