// Suraksha Call Detector Frontend
const CallDetector = {
  samples: {
    fedex: "Hello, this is FedEx Courier Customer Support. An international parcel sent from London to Taiwan under your Aadhaar card has been seized by Mumbai Customs. It contains 5 passports and illegal narcotics drugs. You are placed under digital arrest.",
    arrest: "Main Crime Branch Mumbai Police se Senior Inspector bol raha hoon. Aapke khilaf Money Laundering aur arrest warrant jari hua hai. Phone cut mat karna, ghar ke andar raho aur turant 50000 rupaye bail security bond transfer karo.",
    bank_kyc: "Namaste sir, main SBI customer care se bol raha hoon. Aapka YONO account aur ATM card aaj shaam 5 baje band ho jayega. Turant चालू rakhne ke liye AnyDesk app download kare aur screen share kare."
  },

  init() {
    const btnAnalyze = document.getElementById('btnAnalyzeCall');
    const btnClear = document.getElementById('btnClearCall');
    const audioInput = document.getElementById('callAudioFile');
    const transcriptInput = document.getElementById('callTranscriptInput');

    if (btnAnalyze) {
      btnAnalyze.addEventListener('click', () => this.analyzeCall());
    }
    if (btnClear) {
      btnClear.addEventListener('click', () => {
        if (transcriptInput) transcriptInput.value = '';
        if (audioInput) audioInput.value = '';
        const vBox = document.getElementById('callVerdictBox');
        if (vBox) vBox.classList.remove('show', 'danger', 'warning', 'safe');
      });
    }

    // Call sample chips
    document.querySelectorAll('.sample-chip[data-call-sample]').forEach((chip) => {
      chip.addEventListener('click', () => {
        const k = chip.getAttribute('data-call-sample');
        if (this.samples[k] && transcriptInput) {
          transcriptInput.value = this.samples[k];
          this.analyzeCall();
        }
      });
    });
  },

  async analyzeCall() {
    const audioInput = document.getElementById('callAudioFile');
    const transcriptInput = document.getElementById('callTranscriptInput');

    const file = audioInput && audioInput.files ? audioInput.files[0] : null;
    const text = transcriptInput ? transcriptInput.value.trim() : '';

    if (!file && !text) {
      if (window.App) window.App.showToast('कृपया कॉल रिकॉर्डिंग ऑडियो अपलोड करें या बातचीत पेस्ट करें');
      return;
    }

    const formData = new FormData();
    if (file) formData.append('audio', file);
    if (text) formData.append('transcript', text);
    formData.append('language', I18n.currentLang || 'hi');

    try {
      const res = await fetch('/api/detect/call', { method: 'POST', body: formData });
      const data = await res.json();
      this.renderCallVerdict(data);
    } catch (err) {
      console.warn('Call detection error:', err);
      if (window.App) window.App.showToast('कॉल विश्लेषण में समस्या आई (Offline error)');
    }
  },

  renderCallVerdict(data) {
    const box = document.getElementById('callVerdictBox');
    if (!box) return;

    box.classList.remove('danger', 'warning', 'safe');
    let badgeClass = 'safe';
    let iconSvg = `<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>`;

    if (data.verdict === 'likely_scam') {
      badgeClass = 'danger';
      iconSvg = `<svg viewBox="0 0 24 24"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>`;
    } else if (data.verdict === 'unsure') {
      badgeClass = 'warning';
      iconSvg = `<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 16h-2v-2h2v2zm1.07-7.75l-.9.92C12.45 11.9 12 12.5 12 14h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H7c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.04-.42 1.99-1.07 2.75z"/></svg>`;
    }

    box.classList.add(badgeClass);

    let scriptBannerHtml = '';
    if (data.script_meta) {
      scriptBannerHtml = `
        <div style="background:#fee2e2; border:1.5px solid #ef4444; color:#991b1b; padding:10px; border-radius:8px; font-weight:700; font-size:var(--font-size-sm); margin-bottom:12px;">
          ${data.script_meta.danger_banner}
          <div style="font-size:12px; font-weight:500; margin-top:4px;">${data.script_meta.action_advice}</div>
        </div>
      `;
    }

    const noticeHtml = data.transcription_notice 
      ? `<div style="font-size:11px; color:var(--text-muted); margin-bottom:6px;">ℹ️ ${data.transcription_notice}</div>` 
      : '';

    const maxStage = data.stages ? data.stages.current_stage : 0;
    const stagesHtml = `
      <div class="stage-timeline" style="margin: 10px 0;">
        <div class="stage-step ${maxStage >= 1 ? 'active' : ''}">
          <div class="step-dot">1</div><span>Authority</span>
        </div>
        <div class="stage-step ${maxStage >= 2 ? 'active' : ''}">
          <div class="step-dot">2</div><span>Urgency</span>
        </div>
        <div class="stage-step ${maxStage >= 3 ? 'active' : ''}">
          <div class="step-dot">3</div><span>Sensitive</span>
        </div>
        <div class="stage-step ${maxStage >= 4 ? 'active' : ''}">
          <div class="step-dot">4</div><span>Payment</span>
        </div>
      </div>
    `;

    box.innerHTML = `
      <div class="verdict-header">
        <div class="verdict-icon-large">${iconSvg}</div>
        <div>
          <div class="verdict-title">${I18n.t('verdict_' + data.verdict)}</div>
          <div class="verdict-confidence">Confidence Score: ${data.confidence_percent}%</div>
        </div>
      </div>
      <div class="verdict-body">
        ${noticeHtml}
        ${scriptBannerHtml}
        ${stagesHtml}

        <div style="font-weight: 700; font-size: var(--font-size-sm); margin-bottom: 4px;">कॉल बातचीत (Transcript with Highlights):</div>
        <div class="highlighted-text-box">${data.highlighted_html || data.transcript}</div>

        <p style="font-size: var(--font-size-base); font-weight: 600; margin-top: 8px;">${data.explanation}</p>

        <div class="btn-row" style="margin-top: 14px;">
          <button class="btn btn-secondary" onclick="window.speechSynthesis.speak(new SpeechSynthesisUtterance('${data.explanation}'))">
            🔊 बोलकर सुनाएं
          </button>
          <button class="btn btn-accent" onclick="window.ReportsManager.openModal('Unknown Caller')">
            📢 इस कॉल को रिपोर्ट करें
          </button>
          <button class="btn btn-danger" onclick="if(window.App) window.App.navigate('help')">
            🚨 1930 सहायता लें
          </button>
        </div>
      </div>
    `;

    box.classList.add('show');
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};
