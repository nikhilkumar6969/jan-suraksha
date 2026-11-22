// Suraksha Call Detector Frontend
const CallDetector = {
  samples: {
    fedex: "Hello, this is FedEx Courier Customer Support. An international parcel sent from London to Taiwan under your Aadhaar card has been seized by Mumbai Customs. It contains 5 passports and illegal narcotics drugs. You are placed under digital arrest.",
    arrest: "Main Crime Branch Mumbai Police se Senior Inspector bol raha hoon. Aapke khilaf Money Laundering aur arrest warrant jari hua hai. Phone cut mat karna, ghar ke andar raho aur turant 50000 rupaye bail security bond transfer karo.",
    bank_kyc: "Namaste sir, main SBI customer care se bol raha hoon. Aapka YONO account aur ATM card aaj shaam 5 baje band ho jayega. Turant चालू rakhne ke liye AnyDesk app download kare aur screen share kare."
  },

  audioSamples: {
    digital_arrest: "/assets/samples/digital_arrest_call.wav",
    bank_kyc: "/assets/samples/bank_kyc_call.wav",
    fedex_customs: "/assets/samples/fedex_customs_call.wav"
  },

  speechRecognizer: null,
  isRecordingMic: false,
  activeAudioFile: null,

  init() {
    const btnAnalyze = document.getElementById('btnAnalyzeCall');
    const btnClear = document.getElementById('btnClearCall');
    const audioInput = document.getElementById('callAudioFile');
    const transcriptInput = document.getElementById('callTranscriptInput');
    const btnMic = document.getElementById('btnMicRecordCall');
    const audioPlayer = document.getElementById('callAudioPlayer');

    if (btnAnalyze) {
      btnAnalyze.addEventListener('click', () => this.analyzeCall());
    }

    if (btnClear) {
      btnClear.addEventListener('click', () => {
        if (transcriptInput) transcriptInput.value = '';
        if (audioInput) audioInput.value = '';
        this.activeAudioFile = null;
        if (audioPlayer) {
          audioPlayer.pause();
          audioPlayer.src = '';
          audioPlayer.style.display = 'none';
        }
        this.hideStatus();
        const vBox = document.getElementById('callVerdictBox');
        if (vBox) vBox.classList.remove('show', 'danger', 'warning', 'safe');
      });
    }

    // Audio file selection preview
    if (audioInput) {
      audioInput.addEventListener('change', (e) => {
        const file = e.target.files ? e.target.files[0] : null;
        this.activeAudioFile = file;
        if (file && audioPlayer) {
          audioPlayer.src = URL.createObjectURL(file);
          audioPlayer.style.display = 'block';
        }
      });
    }

    // Call text sample chips
    document.querySelectorAll('.sample-chip[data-call-sample]').forEach((chip) => {
      chip.addEventListener('click', () => {
        const k = chip.getAttribute('data-call-sample');
        if (this.samples[k] && transcriptInput) {
          transcriptInput.value = this.samples[k];
          this.activeAudioFile = null;
          if (audioInput) audioInput.value = '';
          this.analyzeCall();
        }
      });
    });

    // Call audio sample chips
    document.querySelectorAll('.sample-chip[data-audio-sample]').forEach((chip) => {
      chip.addEventListener('click', async () => {
        const key = chip.getAttribute('data-audio-sample');
        await this.loadAudioSample(key);
      });
    });

    // Live Microphone Speech Recognition
    if (btnMic) {
      btnMic.addEventListener('click', () => this.toggleMic());
    }
  },

  async loadAudioSample(key) {
    const url = this.audioSamples[key];
    if (!url) return;

    this.showStatus('⏳ सैंपल ऑडियो लोड हो रहा है...', 'info');
    try {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error('Sample audio fetch failed');
      const blob = await resp.blob();
      const file = new File([blob], `${key}_sample.wav`, { type: 'audio/wav' });
      this.activeAudioFile = file;

      const audioPlayer = document.getElementById('callAudioPlayer');
      if (audioPlayer) {
        audioPlayer.src = URL.createObjectURL(blob);
        audioPlayer.style.display = 'block';
      }

      this.showStatus(`✅ ऑडियो लोड हुआ (${file.name})। ऑफलाइन Vosk से ट्रांसक्रिप्शन शुरू हो रहा है...`, 'success');
      // Trigger analysis directly
      await this.analyzeCall();
    } catch (err) {
      console.error('Failed to load sample audio:', err);
      this.showStatus('ऑडियो लोड करने में त्रुटि आई', 'error');
    }
  },

  toggleMic() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const btnMicText = document.getElementById('micBtnText');
    const transcriptInput = document.getElementById('callTranscriptInput');

    if (!SpeechRecognition) {
      if (window.App) window.App.showToast('आपका ब्राउज़र माइक स्पीच-टू-टेक्स्ट सपोर्ट नहीं करता। कृपया ऑडियो फाइल अपलोड करें।');
      return;
    }

    if (this.isRecordingMic) {
      if (this.speechRecognizer) this.speechRecognizer.stop();
      this.isRecordingMic = false;
      if (btnMicText) btnMicText.textContent = 'माइक से बोलें';
      this.showStatus('माइक रिकॉर्डिंग बंद की गई।', 'info');
      return;
    }

    try {
      this.speechRecognizer = new SpeechRecognition();
      const lang = (window.I18n && window.I18n.currentLang === 'en') ? 'en-IN' : 'hi-IN';
      this.speechRecognizer.lang = lang;
      this.speechRecognizer.continuous = true;
      this.speechRecognizer.interimResults = true;

      this.speechRecognizer.onstart = () => {
        this.isRecordingMic = true;
        if (btnMicText) btnMicText.textContent = '🛑 बोलना बंद करें';
        this.showStatus('🔴 माइक चालू है... कृपया कॉल की बातचीत बोलें (हिंदी/English)', 'info');
      };

      this.speechRecognizer.onresult = (event) => {
        let finalStr = '';
        for (let i = 0; i < event.results.length; ++i) {
          finalStr += event.results[i][0].transcript + ' ';
        }
        if (transcriptInput && finalStr.trim()) {
          transcriptInput.value = finalStr.trim();
        }
      };

      this.speechRecognizer.onerror = (err) => {
        console.warn('Speech recognition error:', err);
        this.isRecordingMic = false;
        if (btnMicText) btnMicText.textContent = 'माइक से बोलें';
        this.showStatus('माइक अनुमति या त्रुटि: ' + (err.error || ''), 'error');
      };

      this.speechRecognizer.onend = () => {
        this.isRecordingMic = false;
        if (btnMicText) btnMicText.textContent = 'माइक से बोलें';
      };

      this.speechRecognizer.start();
    } catch (e) {
      console.error('Mic start error:', e);
      if (window.App) window.App.showToast('माइक चालू करने में त्रुटि: ' + e.message);
    }
  },

  showStatus(msg, type = 'info') {
    const el = document.getElementById('callTranscribeStatus');
    if (!el) return;
    el.style.display = 'block';
    el.textContent = msg;
    if (type === 'error') {
      el.style.background = '#fee2e2';
      el.style.color = '#991b1b';
    } else if (type === 'success') {
      el.style.background = '#dcfce7';
      el.style.color = '#166534';
    } else {
      el.style.background = '#e0f2fe';
      el.style.color = '#0369a1';
    }
  },

  hideStatus() {
    const el = document.getElementById('callTranscribeStatus');
    if (el) el.style.display = 'none';
  },

  async analyzeCall() {
    const audioInput = document.getElementById('callAudioFile');
    const transcriptInput = document.getElementById('callTranscriptInput');

    const file = this.activeAudioFile || (audioInput && audioInput.files ? audioInput.files[0] : null);
    const text = transcriptInput ? transcriptInput.value.trim() : '';

    if (!file && !text) {
      if (window.App) window.App.showToast('कृपया कॉल रिकॉर्डिंग ऑडियो अपलोड करें या बातचीत पेस्ट करें');
      return;
    }

    const formData = new FormData();
    if (file) {
      formData.append('audio', file);
      this.showStatus('🎙️ ऑफलाइन वोस्क (Vosk) मॉडल द्वारा ऑडियो का विश्लेषण हो रहा है... कृपया प्रतीक्षा करें', 'info');
    }
    if (text) formData.append('transcript', text);
    formData.append('language', (window.I18n && window.I18n.currentLang) || 'hi');

    const btnAnalyze = document.getElementById('btnAnalyzeCall');
    if (btnAnalyze) {
      btnAnalyze.disabled = true;
      btnAnalyze.textContent = 'जांच हो रही है...';
    }

    try {
      const res = await fetch('/api/detect/call', { method: 'POST', body: formData });
      const data = await res.json();
      
      // Auto-populate transcript box if server transcribed audio
      if (data.transcript && transcriptInput && !transcriptInput.value.trim()) {
        transcriptInput.value = data.transcript;
      }

      if (data.transcription_notice) {
        this.showStatus('ℹ️ ' + data.transcription_notice, data.transcript ? 'success' : 'info');
      } else {
        this.hideStatus();
      }

      this.renderCallVerdict(data);
    } catch (err) {
      console.warn('Call detection error:', err);
      this.showStatus('कॉल विश्लेषण में समस्या आई (Offline connection error)', 'error');
      if (window.App) window.App.showToast('कॉल विश्लेषण में समस्या आई');
    } finally {
      if (btnAnalyze) {
        btnAnalyze.disabled = false;
        btnAnalyze.innerHTML = '🔍 <span data-i18n="btn_analyze">कॉल का सच जांचें</span>';
      }
    }
  },

  renderCallVerdict(data) {
    const box = document.getElementById('callVerdictBox');
    if (!box) return;

    box.classList.remove('danger', 'warning', 'safe');
    let badgeClass = 'safe';
    let iconSvg = `<svg viewBox="0 0 24 24"><use href="#icon-check"/></svg>`;

    if (data.verdict === 'likely_scam') {
      badgeClass = 'danger';
      iconSvg = `<svg viewBox="0 0 24 24"><use href="#icon-alert-triangle"/></svg>`;
    } else if (data.verdict === 'unsure') {
      badgeClass = 'warning';
      iconSvg = `<svg viewBox="0 0 24 24"><use href="#icon-alert-triangle"/></svg>`;
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
      ? `<div style="font-size:12px; font-weight:600; color:var(--text-muted); margin-bottom:8px;">🎙️ ${data.transcription_notice}</div>` 
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
          <div class="verdict-title">${window.I18n ? window.I18n.t('verdict_' + data.verdict) : data.verdict}</div>
          <div class="verdict-confidence">Confidence Score: ${data.confidence_percent}%</div>
        </div>
      </div>
      <div class="verdict-body">
        ${noticeHtml}
        ${scriptBannerHtml}
        ${stagesHtml}

        <div style="font-weight: 700; font-size: var(--font-size-sm); margin-bottom: 4px;">कॉल बातचीत (Audio Transcript with Scam Highlights):</div>
        <div class="highlighted-text-box">${data.highlighted_html || data.transcript || 'No transcript available.'}</div>

        <p style="font-size: var(--font-size-base); font-weight: 600; margin-top: 8px;">${data.explanation}</p>

        <div class="btn-row" style="margin-top: 14px;">
          <button class="btn btn-secondary" onclick="window.speechSynthesis.speak(new SpeechSynthesisUtterance('${(data.explanation || '').replace(/'/g, "\\'")}'))">
            <svg viewBox="0 0 24 24"><use href="#icon-volume"/></svg>
            बोलकर सुनाएं
          </button>
          <button class="btn btn-accent" onclick="if(window.ReportsManager) window.ReportsManager.openModal('Unknown Caller')">
            <svg viewBox="0 0 24 24"><use href="#icon-alert-triangle"/></svg>
            इस कॉल को रिपोर्ट करें
          </button>
          <button class="btn btn-danger" onclick="if(window.App) window.App.navigate('help')">
            <svg viewBox="0 0 24 24"><use href="#icon-phone"/></svg>
            1930 सहायता लें
          </button>
        </div>
      </div>
    `;

    box.classList.add('show');
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};

window.CallDetector = CallDetector;
document.addEventListener('DOMContentLoaded', () => CallDetector.init());
