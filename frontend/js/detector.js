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

    const btnShare = document.getElementById('btnShareFromVerdict');
    if (btnShare) {
      btnShare.addEventListener('click', () => {
        const text = smsInput ? smsInput.value.trim() : '';
        const vTitle = document.getElementById('verdictTitle')?.textContent || 'Scam Alert';
        const vExpl = document.getElementById('verdictExplanation')?.textContent || '';
        const shareBody = `[Jan Suraksha Alert]\nVerdict: ${vTitle}\nMessage: "${text}"\nDetails: ${vExpl}\nHelpline: 1930 (National Cyber Crime Portal)`;
        
        if (window.SurakshaNative && typeof window.SurakshaNative.shareText === 'function') {
          window.SurakshaNative.shareText('Jan Suraksha Alert', shareBody);
        } else if (navigator.share) {
          navigator.share({ title: 'Jan Suraksha Alert', text: shareBody }).catch(() => {});
        } else if (navigator.clipboard) {
          navigator.clipboard.writeText(shareBody);
          if (window.App) window.App.showToast('चेतावनी कॉपी हो गई (Alert copied to clipboard)');
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

    // 1. If executing inside native Android APK, use embedded on-device ML model directly
    if (window.SurakshaNative && typeof window.SurakshaNative.classifyTextOffline === 'function') {
      try {
        const rawJson = window.SurakshaNative.classifyTextOffline(text);
        const data = JSON.parse(rawJson);
        data.normalized_text = text;
        this.renderVerdict(data);
        return;
      } catch (nativeErr) {
        console.warn('Native on-device classification error, falling back to network/heuristic:', nativeErr);
      }
    }

    // 2. Web / Localhost execution
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
      vIcon.innerHTML = `<svg viewBox="0 0 24 24"><use href="#icon-alert-triangle"/></svg>`;
      if (window.SurakshaNative && typeof window.SurakshaNative.vibrate === 'function') {
        window.SurakshaNative.vibrate(JSON.stringify([250, 100, 250, 100, 400]));
      }
    } else if (data.verdict === 'unsure') {
      box.classList.add('warning');
      vTitle.textContent = I18n.t('verdict_unsure', 'Unsure (संदेहास्पद / Verify with Bank)');
      vIcon.innerHTML = `<svg viewBox="0 0 24 24"><use href="#icon-alert-triangle"/></svg>`;
    } else {
      box.classList.add('safe');
      vTitle.textContent = I18n.t('verdict_genuine', 'Looks Genuine (सामान्य / Safe)');
      vIcon.innerHTML = `<svg viewBox="0 0 24 24"><use href="#icon-check"/></svg>`;
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
