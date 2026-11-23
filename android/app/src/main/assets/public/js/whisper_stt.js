// Offline AI Speech-to-Text Controller using OpenAI Whisper Medium
// Powered by local backend faster-whisper inference

const WhisperSTT = {
  currentBlob: null,
  currentFile: null,
  mediaRecorder: null,
  recordedChunks: [],
  isRecording: false,

  init() {
    const fileInput = document.getElementById('sttAudioFileInput');
    const btnRecord = document.getElementById('btnSttRecord');
    const btnStart = document.getElementById('btnStartTranscription');
    const btnClearAudio = document.getElementById('btnSttClearAudio');
    const btnCopy = document.getElementById('btnSttCopy');
    const btnDownload = document.getElementById('btnSttDownload');
    const btnClear = document.getElementById('btnSttClear');
    const btnSendToDetector = document.getElementById('btnSttSendToDetector');
    const engineModeSelect = document.getElementById('sttEngineModeSelect');

    if (engineModeSelect) {
      engineModeSelect.addEventListener('change', (e) => this.handleModeChange(e.target.value));
    }

    if (fileInput) {
      fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
    }

    if (btnRecord) {
      btnRecord.addEventListener('click', () => this.toggleRecording());
    }

    if (btnStart) {
      btnStart.addEventListener('click', () => this.startTranscription());
    }

    if (btnClearAudio) {
      btnClearAudio.addEventListener('click', () => this.clearAudio());
    }

    if (btnCopy) {
      btnCopy.addEventListener('click', () => this.copyTranscript());
    }

    if (btnDownload) {
      btnDownload.addEventListener('click', () => this.downloadTranscript());
    }

    if (btnClear) {
      btnClear.addEventListener('click', () => this.clearAll());
    }

    if (btnSendToDetector) {
      btnSendToDetector.addEventListener('click', () => this.sendToFraudDetector());
    }
  },

  handleModeChange(mode) {
    const badge = document.getElementById('sttActiveModeBadge');
    const titles = {
      'balanced': 'Balanced (Whisper Small)',
      'accuracy': 'Accuracy (Whisper Medium)',
      'speed': 'Speed (Sherpa-ONNX Tiny)'
    };
    if (badge) badge.textContent = titles[mode] || 'Balanced Mode';
  },

  handleFileSelect(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    this.currentFile = file;
    this.currentBlob = null;

    this.updateAudioPreview(file, file.name, (file.size / (1024 * 1024)).toFixed(2) + ' MB');
  },

  async toggleRecording() {
    if (this.isRecording) {
      this.stopRecording();
    } else {
      await this.startRecording();
    }
  },

  async startRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      if (window.App) window.App.showToast('माइक्रोफ़ोन इस डिवाइस में उपलब्ध नहीं है (Microphone not supported)');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.recordedChunks = [];

      let mimeType = 'audio/webm';
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' : '';
      }

      this.mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          this.recordedChunks.push(e.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.recordedChunks, { type: mimeType || 'audio/webm' });
        this.currentBlob = audioBlob;
        this.currentFile = null;

        const sizeMb = (audioBlob.size / (1024 * 1024)).toFixed(2) + ' MB';
        this.updateAudioPreview(audioBlob, 'Microphone_Recording.webm', sizeMb);

        // Stop all audio tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      this.mediaRecorder.start(250);
      this.isRecording = true;

      // Update UI for recording state
      const btn = document.getElementById('btnSttRecord');
      const text = document.getElementById('sttRecordBtnText');
      if (btn) btn.classList.add('btn-danger');
      if (text) text.textContent = '⏹ रिकॉर्डिंग रोकें (Stop Recording)';

      const statusBox = document.getElementById('sttAudioStatusBox');
      const statusText = document.getElementById('sttAudioStatusText');
      const statusIcon = document.getElementById('sttAudioStatusIcon');
      if (statusBox) statusBox.style.display = 'block';
      if (statusIcon) statusIcon.textContent = '🔴';
      if (statusText) statusText.textContent = 'माइक्रोफ़ोन से रिकॉर्ड किया जा रहा है... (Recording in progress)';

      if (window.App) window.App.showToast('🎙️ रिकॉर्डिंग शुरू हो गई है (Recording started)');
    } catch (err) {
      console.error('Microphone access denied:', err);
      if (window.App) window.App.showToast('माइक्रोफ़ोन परमिशन नहीं मिली (Microphone permission denied)');
    }
  },

  stopRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;

      const btn = document.getElementById('btnSttRecord');
      const text = document.getElementById('sttRecordBtnText');
      if (btn) btn.classList.remove('btn-danger');
      if (text) text.textContent = 'माइक से रिकॉर्ड करें (Record)';

      if (window.App) window.App.showToast('✅ रिकॉर्डिंग पूरी हुई (Recording saved)');
    }
  },

  updateAudioPreview(source, name, sizeStr) {
    const box = document.getElementById('sttAudioStatusBox');
    const text = document.getElementById('sttAudioStatusText');
    const badge = document.getElementById('sttAudioSizeBadge');
    const preview = document.getElementById('sttAudioPreview');
    const btnClearAudio = document.getElementById('btnSttClearAudio');
    const icon = document.getElementById('sttAudioStatusIcon');

    if (!box) return;

    box.style.display = 'block';
    if (icon) icon.textContent = '🎵';
    if (text) text.textContent = name;
    if (badge) badge.textContent = sizeStr;
    if (btnClearAudio) btnClearAudio.style.display = 'inline-flex';

    if (preview) {
      preview.src = URL.createObjectURL(source);
      preview.style.display = 'block';
    }
  },

  clearAudio() {
    this.currentBlob = null;
    this.currentFile = null;
    this.isRecording = false;

    const fileInput = document.getElementById('sttAudioFileInput');
    if (fileInput) fileInput.value = '';

    const preview = document.getElementById('sttAudioPreview');
    if (preview) {
      preview.pause();
      preview.src = '';
      preview.style.display = 'none';
    }

    const box = document.getElementById('sttAudioStatusBox');
    if (box) box.style.display = 'none';

    const btnClearAudio = document.getElementById('btnSttClearAudio');
    if (btnClearAudio) btnClearAudio.style.display = 'none';
  },

  async startTranscription() {
    const audioPayload = this.currentBlob || this.currentFile;
    if (!audioPayload) {
      if (window.App) window.App.showToast('कृपया पहले ऑडियो फ़ाइल चुनें या रिकॉर्ड करें (Please select or record audio)');
      return;
    }

    const langSelect = document.getElementById('sttLanguageSelect');
    const langValue = langSelect ? langSelect.value : 'auto';
    const modeSelect = document.getElementById('sttEngineModeSelect');
    const modeValue = modeSelect ? modeSelect.value : 'balanced';

    const processingBox = document.getElementById('sttProcessingBox');
    const procTitle = document.getElementById('sttProcessingTitle');
    const resultCard = document.getElementById('sttResultCard');
    const btnStart = document.getElementById('btnStartTranscription');

    if (procTitle) {
      if (modeValue === 'accuracy') {
        procTitle.textContent = 'Whisper Medium (Accuracy) मॉडल प्रोसेस कर रहा है...';
      } else if (modeValue === 'speed') {
        procTitle.textContent = 'Sherpa-ONNX Tiny (Speed) मॉडल प्रोसेस कर रहा है...';
      } else {
        procTitle.textContent = 'Whisper Small (Balanced) मॉडल प्रोसेस कर रहा है...';
      }
    }

    if (processingBox) processingBox.style.display = 'block';
    if (resultCard) resultCard.style.display = 'none';
    if (btnStart) btnStart.disabled = true;

    try {
      const formData = new FormData();
      const filename = this.currentFile ? this.currentFile.name : 'recording.webm';
      formData.append('audio', audioPayload, filename);
      formData.append('mode', modeValue);

      if (langValue && langValue !== 'auto') {
        formData.append('language', langValue);
      }

      const response = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Transcription failed on server');
      }

      this.renderResult(data);
      if (window.App) window.App.showToast('✅ ट्रांसक्रिप्शन पूर्ण (Transcription complete)');
    } catch (err) {
      console.error('Transcription error:', err);
      if (window.App) window.App.showToast('त्रुटि: ' + (err.message || 'ट्रांसक्रिप्शन विफल'));
    } finally {
      if (processingBox) processingBox.style.display = 'none';
      if (btnStart) btnStart.disabled = false;
    }
  },

  renderResult(data) {
    const resultCard = document.getElementById('sttResultCard');
    const textEl = document.getElementById('sttTranscriptionText');
    const engineBadge = document.getElementById('sttEngineBadge');
    const langBadge = document.getElementById('sttDetectedLangBadge');
    const durationBadge = document.getElementById('sttDurationBadge');
    const timeBadge = document.getElementById('sttTimeBadge');
    const statusBadge = document.getElementById('sttStatusBadge');

    if (!resultCard || !textEl) return;

    textEl.textContent = data.text || '(कोई स्पष्ट ध्वनि नहीं मिली / No speech detected)';

    const langNames = {
      'hi': 'हिंदी (Hindi)',
      'en': 'English',
      'chg': 'छत्तीसगढ़ी / Hindi',
      'mr': 'मराठी (Marathi)',
      'bn': 'বাংলা (Bengali)'
    };

    const displayLang = langNames[data.language] || data.language || 'Auto';
    const probPercent = data.language_probability ? Math.round(data.language_probability * 100) : 100;

    if (engineBadge) {
      const engineLabels = {
        'accuracy': 'Whisper Medium (769M)',
        'balanced': 'Whisper Small (244M)',
        'speed': 'Sherpa-ONNX Tiny (39M)'
      };
      engineBadge.textContent = `इंजन: ${data.engine || engineLabels[data.mode] || 'Whisper'}`;
    }

    if (langBadge) {
      langBadge.textContent = `भाषा: ${displayLang} (${probPercent}%)`;
    }

    if (durationBadge) {
      durationBadge.textContent = `अवधि: ${data.duration || 0}s`;
    }

    if (timeBadge) {
      const procTime = data.processing_time !== undefined ? `${data.processing_time}s` : '-';
      const rtfText = data.rtf !== undefined ? ` (RTF: ${data.rtf}x)` : '';
      timeBadge.textContent = `समय: ${procTime}${rtfText}`;
    }

    if (statusBadge) {
      statusBadge.textContent = '✅ पूर्ण (Completed)';
    }

    resultCard.style.display = 'block';
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  },

  copyTranscript() {
    const textEl = document.getElementById('sttTranscriptionText');
    if (!textEl || !textEl.textContent.trim()) return;

    const text = textEl.textContent.trim();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        if (window.App) window.App.showToast('📋 टेक्स्ट कॉपी हो गया (Transcript copied)');
      });
    }
  },

  downloadTranscript() {
    const textEl = document.getElementById('sttTranscriptionText');
    if (!textEl || !textEl.textContent.trim()) return;

    const text = textEl.textContent.trim();
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `whisper_transcript_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    if (window.App) window.App.showToast('📥 फ़ाइल डाउनलोड हो गई (Transcript downloaded as TXT)');
  },

  clearAll() {
    const textEl = document.getElementById('sttTranscriptionText');
    if (textEl) textEl.textContent = '';

    const resultCard = document.getElementById('sttResultCard');
    if (resultCard) resultCard.style.display = 'none';

    this.clearAudio();
  },

  sendToFraudDetector() {
    const textEl = document.getElementById('sttTranscriptionText');
    if (!textEl || !textEl.textContent.trim()) return;

    const text = textEl.textContent.trim();
    if (window.App) {
      window.App.switchSubtab('subtab-sms');
      const smsInput = document.getElementById('smsInput');
      if (smsInput) {
        smsInput.value = text;
        const btn = document.getElementById('btnAnalyzeSms');
        if (btn) btn.click();
      }
    }
  }
};

window.WhisperSTT = WhisperSTT;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => WhisperSTT.init());
} else {
  WhisperSTT.init();
}
