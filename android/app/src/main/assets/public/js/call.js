// Suraksha Real-Time Offline AI Scam Call Guardian Frontend
// Features: Sherpa-ONNX streaming ASR, Silero VAD, 5-stage timeline tracking,
// contextual fraud intent detection, multi-lingual offline TTS, 3 warning tiers.

const CallDetector = {
  // Pre-configured Test Scenarios for instant evaluation
  scenarios: {
    otp_demand: {
      title: "1. OTP Request Fraud",
      text: "Sir, I am calling from head office verification department. Please tell your 6-digit OTP right now to complete your verification.",
      lang: "en"
    },
    upi_pin_demand: {
      title: "2. UPI PIN Cashback Hazard",
      text: "Congratulations! You have received cashback of 5000 rupees. To accept the money in your bank account, enter your UPI PIN now.",
      lang: "en"
    },
    fake_bank: {
      title: "3. Fake Bank Employee & KYC Threat",
      text: "Namaste sir, main SBI customer care se bol raha hoon. Aapka YONO account aur ATM card aaj shaam 5 baje band ho jayega. Turant चालू rakhne ke liye AnyDesk app download kare aur screen share kare.",
      lang: "hi"
    },
    digital_arrest: {
      title: "4. Fake Police / Digital Arrest",
      text: "Main Crime Branch Mumbai Police se Senior Inspector bol raha hoon. Aapke Aadhaar card par illegal parcel mila hai jisme drugs hain. Aap digital arrest me hain, phone cut mat karna aur turant 50000 rupaye bail security bond transfer karo.",
      lang: "hi"
    },
    fake_subsidy: {
      title: "5. Fake Subsidy Scheme (Mahtari Vandan)",
      text: "नमस्कार, महतारी वंदन योजना के 1000 रुपया तोर खाता म आए बर अटके हे। योजना के राशि पाए बर तुरते 200 रुपया सत्यापन शुल्क जमा करव अउ अपन गुप्त ओटीपी बताव।",
      lang: "chg"
    },
    money_demand: {
      title: "6. Demands Money / Clearance Fee",
      text: "This is international customs clearance. Your package has been detained. Transfer clearance fee of Rs 15000 immediately to release the consignment.",
      lang: "en"
    },
    remote_access: {
      title: "7. Remote Access APK Fraud",
      text: "Aapke phone me technical issue hai. Humne support file bheja hai, WhatsApp se unknown APK install kare aur QuickSupport me screen share allow karein.",
      lang: "hi"
    },
    normal_otp: {
      title: "8. Normal Conversation (Swiggy Safe Narration)",
      text: "Maine Swiggy ka OTP khud app me enter kiya aur delivery boy ko khana de gaya. Normal order tha.",
      lang: "hi"
    },
    normal_banking: {
      title: "9. Normal Conversation (Passbook Update)",
      text: "Kal subah bank jaunga passbook update karane ke liye. Manager sahab se milkar cheque book le aaunga.",
      lang: "hi"
    },
    cg_bijli: {
      title: "10. Chhattisgarhi Electricity Threat",
      text: "नमस्कार, तोर बिजली बिल नइ भरे हस। आज संझा 9:30 बजे तोर घर के बिजली लाइन कट जाही। लाइन कटने ले बचाए बर तुरते 9827012345 म फोन लगाके पईसा पटाव।",
      lang: "chg"
    },
    cg_police: {
      title: "11. Chhattisgarhi Thana & Warrant",
      text: "थाना कोतवाली रायपुर ले बोलत हंव। तोर नाम म गैर जमानती वारंट निकल गे हे। कॉल ल झन काटव, वीडियो कॉल म बने रहव अउ तुरते 40000 पईसा जमा करव नइ ते जेल भेज देबो।",
      lang: "chg"
    },
    utility_hindi: {
      title: "12. Electricity Power Cut Threat (Hindi)",
      text: "प्रिय उपभोक्ता, आपका पिछला बिजली बिल अपडेट नहीं हुआ है। आज रात 9:30 बजे बिजली कनेक्शन काट दिया जाएगा। तुरंत इस नंबर 9827012345 पर कॉल करके बिल जमा करें।",
      lang: "hi"
    },
    fedex_customs: {
      title: "13. FedEx Customs Seizure (English)",
      text: "This is FedEx International Courier Department. Your parcel containing illegal narcotics and passports has been seized by customs officials. Press 1 to speak with Investigation Officer or pay customs penalty now.",
      lang: "en"
    },
    job_like_fraud: {
      title: "14. YouTube Like & Part-Time Job Scam",
      text: "घर बैठे रोजाना 3000 से 5000 रुपये कमाएं। केवल यूट्यूब वीडियो लाइक करें और टेलीग्राम ग्रुप जॉइन करके 500 रुपये रजिस्ट्रेशन फीस तुरंत जमा करें।",
      lang: "hi"
    },
    kbc_lottery: {
      title: "15. KBC 25 Lakh Lottery Fraud",
      text: "बधाई हो! आपको कौन बनेगा करोड़पति से 25 लाख रुपये की लॉटरी लगी है। पुरस्कार राशि अपने बैंक खाते में ट्रांसफर कराने के लिए 12500 रुपये फाइल चार्ज तुरंत भेजें।",
      lang: "hi"
    },
    safe_helpline: {
      title: "16. 1930 Cyber Fraud Helpline Safe Inquiry",
      text: "क्या ऑनलाइन ठगी होने पर तुरंत 1930 राष्ट्रीय साइबर हेल्पलाइन पर कॉल करके खाता और पैसा फ्रीज कराया जा सकता है?",
      lang: "hi"
    }
  },

  audioSamples: {
    digital_arrest: "/assets/samples/digital_arrest_call.wav",
    bank_kyc: "/assets/samples/bank_kyc_call.wav",
    fedex_customs: "/assets/samples/fedex_customs_call.wav"
  },

  // State management
  isListening: false,
  streamSessionId: null,
  mediaStream: null,
  mediaRecorder: null,
  audioContext: null,
  audioWorkletNode: null,
  mediaStreamSource: null,
  webSocket: null,
  webSocketConnected: false,
  chunkIntervalTimer: null,
  durationTimer: null,
  secondsElapsed: 0,
  speechRecognizer: null,
  activeAudioFile: null,
  lastSpokenWarning: "",
  audioWarningEnabled: true,
  currentAudioPlayer: null,
  isPlayingAlert: false,
  lastAnalysisData: null,
  lastStageData: null,
  silenceTimer: null,

  resetSilenceTimer() {
    if (this.silenceTimer) clearTimeout(this.silenceTimer);
    if (!this.isListening) return;
    this.silenceTimer = setTimeout(() => {
      if (this.isListening) {
        console.log('[CallGuardian] 45s silence timeout reached - stopping mic');
        this.stopLiveListening();
        if (window.App) {
          window.App.showToast('माइक स्वतः बंद हुआ (45 सेकंड निष्क्रियता के बाद)', 3000);
        }
      }
    }, 45000);
  },

  init() {
    this.bindButtons();
    this.bindScenarios();
    this.bindAudioSamples();
    this.checkMicrophonePermission();

    // Auto-stop mic on page unload / hide
    window.addEventListener('beforeunload', () => this.stopLiveListening());
    window.addEventListener('pagehide', () => this.stopLiveListening());

    // Critical modal close button
    const btnCloseCrit = document.getElementById('btnCloseCritWarning');
    if (btnCloseCrit) {
      btnCloseCrit.addEventListener('click', () => {
        const modal = document.getElementById('criticalWarningModal');
        if (modal) modal.style.display = 'none';
      });
    }

    // Notify Family Button
    const btnNotify = document.getElementById('btnNotifyFamily');
    if (btnNotify) {
      btnNotify.addEventListener('click', () => this.triggerFamilyAlert());
    }

    // Audio Warning Checkbox
    const chkAudio = document.getElementById('chkAudioWarning');
    if (chkAudio) {
      chkAudio.addEventListener('change', (e) => {
        this.audioWarningEnabled = e.target.checked;
      });
    }

    // Test Audio Warning Button
    const btnTestTTS = document.getElementById('btnTestAudioWarning');
    if (btnTestTTS) {
      btnTestTTS.addEventListener('click', () => {
        const curLang = (window.I18n && window.I18n.currentLang) || 'hi';
        this.playAudioAlert({
          matched_categories: ['upi_pin_fraud'],
          audio_warning_hi: "सावधान! किसी को भी अपना OTP या UPI PIN न बताएं। पैसे पाने के लिए कभी PIN की आवश्यकता नहीं होती।",
          audio_warning_chg: "सचेत रहव! ककरो ले अपन OTP या UPI पिन झन बतावव। पईसा पाए बर कभू पिन नइ डारे लगत।",
          audio_warning_en: "Caution! Never disclose your OTP or UPI PIN. Receiving money never requires a PIN."
        }, curLang);
      });
    }

    // Sync audio language select and global i18n
    const callAudioLang = document.getElementById('callAudioLang');
    if (callAudioLang) {
      callAudioLang.addEventListener('change', (e) => {
        const val = e.target.value;
        if (val !== 'auto' && window.I18n && window.I18n.currentLang !== val) {
          window.I18n.setLanguage(val);
        }
      });
    }

    // Listen to global language changed event
    window.addEventListener('languageChanged', (e) => {
      this.onLanguageChanged(e.detail ? e.detail.lang : ((window.I18n && window.I18n.currentLang) || 'hi'));
    });

    // Initial language setup for timeline and badges
    this.onLanguageChanged((window.I18n && window.I18n.currentLang) || 'hi');
  },

  bindButtons() {
    // Mode Switcher: Live Call Shield vs Check Recording
    const btnModeLive = document.getElementById('btnModeLiveCall');
    const btnModeUpload = document.getElementById('btnModeUploadAudio');
    const liveSection = document.getElementById('callLiveControlsSection');
    const uploadSection = document.getElementById('callUploadSection');

    if (btnModeLive && btnModeUpload && liveSection && uploadSection) {
      btnModeLive.addEventListener('click', () => {
        btnModeLive.classList.add('active');
        btnModeLive.setAttribute('aria-selected', 'true');
        btnModeUpload.classList.remove('active');
        btnModeUpload.setAttribute('aria-selected', 'false');
        liveSection.style.display = 'block';
        uploadSection.style.display = 'none';
        const player = document.getElementById('callAudioPlayer');
        if (player) player.pause();
      });

      btnModeUpload.addEventListener('click', () => {
        btnModeUpload.classList.add('active');
        btnModeUpload.setAttribute('aria-selected', 'true');
        btnModeLive.classList.remove('active');
        btnModeLive.setAttribute('aria-selected', 'false');
        uploadSection.style.display = 'block';
        liveSection.style.display = 'none';
        if (this.isListening) {
          this.stopLiveListening();
        }
      });
    }

    // Primary Live Call Listen Toggle
    const btnListen = document.getElementById('btnLiveCallListen');
    if (btnListen) {
      btnListen.addEventListener('click', () => this.toggleLiveListening());
    }

    // Speak Call Verdict Action
    const btnSpeakVerdict = document.getElementById('btnSpeakCallVerdict');
    if (btnSpeakVerdict) {
      btnSpeakVerdict.addEventListener('click', () => {
        const expl = document.getElementById('callExplanationText');
        const currentLang = (window.I18n && window.I18n.currentLang) || 'hi';
        if (expl && expl.textContent) {
          this.speakWarning(expl.textContent, currentLang === 'en' ? 'en' : 'hi');
        }
      });
    }

    // Legacy File & Manual Analyze buttons
    const btnAnalyze = document.getElementById('btnAnalyzeCall');
    const btnClear = document.getElementById('btnClearCall');
    const audioInput = document.getElementById('callAudioFile');

    if (btnAnalyze) {
      btnAnalyze.addEventListener('click', () => this.analyzeCall());
    }

    if (btnClear) {
      btnClear.addEventListener('click', () => this.resetAll());
    }

    const btnCopy = document.getElementById('btnCopyCallTranscript');
    if (btnCopy) {
      btnCopy.addEventListener('click', () => {
        const input = document.getElementById('callTranscriptInput');
        if (input && input.value) {
          navigator.clipboard.writeText(input.value).then(() => {
            btnCopy.textContent = '✅ कॉपी हुआ!';
            setTimeout(() => { btnCopy.textContent = '📋 कॉपी करें'; }, 2000);
          }).catch(() => {
            input.select();
            document.execCommand('copy');
            btnCopy.textContent = '✅ कॉपी हुआ!';
            setTimeout(() => { btnCopy.textContent = '📋 कॉपी करें'; }, 2000);
          });
        }
      });
    }

    if (audioInput) {
      audioInput.addEventListener('change', async (e) => {
        const file = e.target.files ? e.target.files[0] : null;
        this.activeAudioFile = file;
        const player = document.getElementById('callAudioPlayer');
        if (file && player) {
          player.src = URL.createObjectURL(file);
          player.style.display = 'block';
        }
        if (file) {
          this.showStatus('ऑडियो से बातचीत निकाली जा रही है (Extracting voice to text)...', 'info');
          await this.analyzeCall();
        }
      });
    }
  },

  bindScenarios() {
    document.querySelectorAll('.sample-chip[data-scenario]').forEach((chip) => {
      chip.addEventListener('click', () => {
        const key = chip.getAttribute('data-scenario');
        const sc = this.scenarios[key];
        if (!sc) return;

        const transcriptInput = document.getElementById('callTranscriptInput');
        if (transcriptInput) transcriptInput.value = sc.text;

        const effectiveLang = (window.I18n && window.I18n.currentLang) || 'hi';
        this.simulateScenarioRun(sc.text, effectiveLang);
      });
    });
  },

  bindAudioSamples() {
    document.querySelectorAll('.sample-chip[data-audio-sample]').forEach((chip) => {
      chip.addEventListener('click', async () => {
        const key = chip.getAttribute('data-audio-sample');
        await this.loadAudioSample(key);
      });
    });
  },

  async checkMicrophonePermission() {
    const pill = document.getElementById('micPermPill');
    if (!navigator.permissions || !navigator.permissions.query) {
      if (pill) {
        pill.textContent = '🎙️ माइक: बंद (Mic OFF)';
        pill.classList.remove('active', 'recording', 'danger');
        pill.classList.add('idle');
      }
      return;
    }
    try {
      const perm = await navigator.permissions.query({ name: 'microphone' });
      this.updateMicPermissionPill(perm.state);
      perm.onchange = () => this.updateMicPermissionPill(perm.state);
    } catch (e) {
      if (pill) {
        pill.textContent = '🎙️ माइक: बंद (Mic OFF)';
        pill.classList.remove('active', 'recording', 'danger');
        pill.classList.add('idle');
      }
    }
  },

  updateMicPermissionPill(state) {
    const pill = document.getElementById('micPermPill');
    if (!pill) return;
    if (this.isListening) {
      pill.textContent = '🔴 माइक: सक्रिय (RECORDING)';
      pill.classList.remove('idle', 'danger');
      pill.classList.add('recording');
    } else if (state === 'denied') {
      pill.textContent = '🎙️ माइक: अनुमति अस्वीकृत (Denied)';
      pill.classList.remove('active', 'recording', 'idle');
      pill.classList.add('danger');
    } else {
      // Microphone is completely idle and off
      pill.textContent = '🎙️ माइक: बंद (Mic OFF)';
      pill.classList.remove('active', 'recording', 'danger');
      pill.classList.add('idle');
    }
  },

  async toggleLiveListening() {
    if (this.isListening) {
      this.stopLiveListening();
    } else {
      await this.startLiveListening();
    }
  },

  async startLiveListening() {
    const btn = document.getElementById('btnLiveCallListen');
    const btnText = document.getElementById('liveListenBtnText');
    const termArea = document.getElementById('liveStreamingTextArea');
    const vadPill = document.getElementById('vadStatusPill');

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      this.updateMicPermissionPill('granted');
    } catch (err) {
      console.error('Microphone access denied:', err);
      this.updateMicPermissionPill('denied');
      if (window.App) {
        window.App.showToast('माइक अनुमति अस्वीकृत: कृपया ब्राउज़र सेटिंग्स में माइक्रोफ़ोन की अनुमति दें।', 4000);
      }
      return;
    }

    this.isListening = true;
    this.updateMicPermissionPill('granted');
    const pulseDot = document.getElementById('livePulseDot');
    if (pulseDot) pulseDot.classList.add('active');
    const statusText = document.getElementById('liveStatusText');
    if (statusText) statusText.textContent = 'लाइव बातचीत (माइक सुन रहा है...)';

    // Notify native Android CallGuardianService foreground service if running inside APK
    if (window.SurakshaNative && window.SurakshaNative.startCallGuardian) {
      const curAudioLang = (document.getElementById('callAudioLang')?.value) || 'auto';
      window.SurakshaNative.startCallGuardian(curAudioLang);
    }
    this.streamSessionId = `call_${Date.now()}`;
    this.secondsElapsed = 0;

    if (btn) {
      btn.classList.remove('idle');
      btn.classList.add('listening');
    }
    if (btnText) btnText.textContent = '🛑 सुनना बंद करें (Stop Listening)';
    if (termArea) {
      termArea.innerHTML = '<span style="color: #38bdf8;">[Sherpa-ONNX Real-Time Engine Active] माइक सुन रहा है...</span>\n';
    }
    if (vadPill) {
      vadPill.textContent = '🟢 VAD: आवाज़ सुन रहे हैं';
      vadPill.classList.add('active');
    }

    this.resetSilenceTimer();

    // Start live timer
    const timerLabel = document.getElementById('liveDurationTimer');
    this.durationTimer = setInterval(() => {
      this.secondsElapsed++;
      const m = String(Math.floor(this.secondsElapsed / 60)).padStart(2, '0');
      const s = String(this.secondsElapsed % 60).padStart(2, '0');
      if (timerLabel) timerLabel.textContent = `${m}:${s}`;
    }, 1000);

    // Primary: Zero-Copy Raw PCM 16kHz AudioWorklet + WebSocket Pipeline
    try {
      await this.setupWebSocketAudioWorkletStreaming();
    } catch (workletErr) {
      console.warn('AudioWorklet/WebSocket streaming fallback notice:', workletErr);
      this.setupAudioChunkStreamingFallback();
    }

    // Setup optional browser SpeechRecognition interim preview if available
    this.setupInterimSpeechPreview();
  },

  async setupWebSocketAudioWorkletStreaming() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/calls/stream`;
    
    // 1. Establish WebSocket
    this.webSocket = new WebSocket(wsUrl);
    this.webSocket.binaryType = 'arraybuffer';

    const langSelect = document.getElementById('callAudioLang');
    const selectedLang = (langSelect && langSelect.value) || 'auto';

    this.webSocket.onopen = () => {
      this.webSocketConnected = true;
      if (this.webSocket.readyState === WebSocket.OPEN) {
        this.webSocket.send(JSON.stringify({
          type: 'config',
          session_id: this.streamSessionId,
          language: selectedLang,
          sample_rate: 16000
        }));
      }
    };

    this.webSocket.onmessage = (event) => {
      if (!this.isListening) return;
      try {
        const data = JSON.parse(event.data);
        if (data.status === 'stopped') return;
        this.handleStreamingResponse(data);
      } catch (err) {
        console.debug('WS parse notice:', err);
      }
    };

    this.webSocket.onerror = (err) => {
      console.warn('WebSocket streaming notice:', err);
      this.webSocketConnected = false;
    };

    this.webSocket.onclose = () => {
      this.webSocketConnected = false;
    };

    // 2. Setup AudioContext and AudioWorklet Processor (16kHz PCM)
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx || !AudioCtx.prototype.audioWorklet) {
      throw new Error('AudioWorklet not supported in this browser');
    }

    this.audioContext = new AudioCtx({ sampleRate: 16000 });
    await this.audioContext.audioWorklet.addModule('/js/pcm-recorder-processor.js');

    this.mediaStreamSource = this.audioContext.createMediaStreamSource(this.mediaStream);
    this.audioWorkletNode = new AudioWorkletNode(this.audioContext, 'pcm-recorder-processor');

    this.audioWorkletNode.port.onmessage = (event) => {
      if (!this.isListening) return;
      const pcmBuffer = event.data; // ArrayBuffer of Int16 16kHz mono PCM

      if (this.webSocket && this.webSocket.readyState === WebSocket.OPEN) {
        this.webSocket.send(pcmBuffer);
      } else if (!this.webSocketConnected) {
        this.sendPcmChunkFallback(pcmBuffer);
      }
    };

    this.mediaStreamSource.connect(this.audioWorkletNode);
    // Connect to destination through a silent gain node to ensure processor keeps ticking
    const silentGain = this.audioContext.createGain();
    silentGain.gain.value = 0.0;
    this.audioWorkletNode.connect(silentGain);
    silentGain.connect(this.audioContext.destination);
  },

  async sendPcmChunkFallback(pcmBuffer) {
    if (!this.isListening) return;
    const langSelect = document.getElementById('callAudioLang');
    const selectedLang = (langSelect && langSelect.value) || 'auto';

    const blob = new Blob([pcmBuffer], { type: 'application/octet-stream' });
    const formData = new FormData();
    formData.append('audio_chunk', blob, 'chunk.raw');
    formData.append('session_id', this.streamSessionId || 'default');
    formData.append('language', selectedLang);
    formData.append('sample_rate', '16000');

    try {
      const resp = await fetch('/api/calls/stream-chunk', { method: 'POST', body: formData });
      if (!resp.ok) return;
      const data = await resp.json();
      this.handleStreamingResponse(data);
    } catch (err) {
      console.debug('PCM fallback chunk error:', err);
    }
  },

  setupAudioChunkStreamingFallback() {
    if (!this.mediaStream) return;

    let mimeType = 'audio/webm;codecs=opus';
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '';
    }

    try {
      this.mediaRecorder = mimeType ? new MediaRecorder(this.mediaStream, { mimeType }) : new MediaRecorder(this.mediaStream);
    } catch (e) {
      this.mediaRecorder = new MediaRecorder(this.mediaStream);
    }

    this.mediaRecorder.ondataavailable = async (e) => {
      if (e.data && e.data.size > 0 && this.isListening) {
        await this.sendAudioChunkToBackend(e.data);
      }
    };

    this.mediaRecorder.start();
    if (this.chunkIntervalTimer) clearInterval(this.chunkIntervalTimer);
    this.chunkIntervalTimer = setInterval(() => {
      if (this.isListening && this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.stop();
        this.mediaRecorder.start();
      }
    }, 1200);
  },

  setupInterimSpeechPreview() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    try {
      this.speechRecognizer = new SpeechRecognition();
      const langSelect = document.getElementById('callAudioLang');
      const langVal = (langSelect && langSelect.value) || 'auto';
      this.speechRecognizer.lang = (langVal === 'en') ? 'en-IN' : 'hi-IN';
      this.speechRecognizer.continuous = true;
      this.speechRecognizer.interimResults = true;

      this.speechRecognizer.onresult = (event) => {
        this.resetSilenceTimer();
        let interimText = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          interimText += event.results[i][0].transcript + ' ';
        }
        if (interimText.trim()) {
          this.renderLiveTranscriptInterim(interimText.trim());
          // Also feed interim text for fast local rule evaluation
          this.evaluateLiveText(interimText.trim());
        }
      };

      this.speechRecognizer.onend = () => {
        if (!this.isListening && this.speechRecognizer) {
          try { this.speechRecognizer.abort(); } catch (e) {}
          this.speechRecognizer = null;
        }
      };

      this.speechRecognizer.onerror = (e) => {
        console.debug('Speech recognition preview notice:', e);
      };

      this.speechRecognizer.start();
    } catch (e) {
      console.debug('Interim speech recognition notice:', e);
    }
  },

  async sendAudioChunkToBackend(blobChunk) {
    if (!this.isListening) return;

    const langSelect = document.getElementById('callAudioLang');
    const selectedLang = (langSelect && langSelect.value) || 'auto';

    const formData = new FormData();
    const ext = blobChunk.type.includes('webm') ? 'webm' : (blobChunk.type.includes('ogg') ? 'ogg' : 'wav');
    formData.append('audio_chunk', blobChunk, `chunk.${ext}`);
    formData.append('session_id', this.streamSessionId || 'default');
    formData.append('language', selectedLang);
    formData.append('sample_rate', '16000');

    try {
      const resp = await fetch('/api/calls/stream-chunk', {
        method: 'POST',
        body: formData
      });
      if (!resp.ok) return;
      const data = await resp.json();

      // Update UI with real-time recognition & scam evaluation
      this.handleStreamingResponse(data);
    } catch (err) {
      console.debug('Chunk upload error:', err);
    }
  },

  handleStreamingResponse(data) {
    if (!this.isListening && !data.force_update) return;
    this.resetSilenceTimer();

    // 1. Update Transcription Terminal & Input Field
    const recognizedText = data.text || data.transcript || '';
    const interimText = data.interim || '';
    if (recognizedText || interimText) {
      this.renderLiveTranscriptCumulative(recognizedText, interimText);
    }

    // 2. Update Latency and VAD pills
    const latencyBadge = document.getElementById('liveLatencyBadge');
    if (latencyBadge && data.latency_ms !== undefined) {
      latencyBadge.textContent = `${data.latency_ms}ms latency (Sherpa-ONNX)`;
    }

    const vadPill = document.getElementById('vadStatusPill');
    if (vadPill && data.speech_detected !== undefined) {
      if (data.speech_detected) {
        vadPill.textContent = '🟢 VAD: आवाज़ सक्रिय';
        vadPill.classList.add('active');
      } else {
        vadPill.textContent = '⚪ VAD: शांति / प्रतीक्षा';
        vadPill.classList.remove('active');
      }
    }

    // 3. Update Risk Banner & 5-Stage Timeline
    if (data.risk_level) {
      this.updateRiskBanner(data);
    }

    // 4. Update Impersonation Escalation Alert
    this.updateClaimContradictions(data.claim_contradictions || []);

    // 5. Tiered Warning Interventions
    this.handleWarningInterventions(data);
  },

  cleanRepeatedTokens(text) {
    if (!text || typeof text !== 'string') return '';
    let cleaned = text;

    // 1. Collapse duplicate consecutive sentences: "Sentence. Sentence." -> "Sentence."
    cleaned = cleaned.replace(/([^.?!]+[.?!])(?:\s*\1)+/gi, (match, p1) => p1);

    // 2. Strip trailing repeated filler hallucinations (e.g. 2+ repeats of 'Good.', 'Thank you.', etc.)
    cleaned = cleaned.replace(/(?:\s*(?:Good|Thank you|Bye|Okay|Yes|No)[.!?]?){2,}\s*$/gi, '');

    // 3. Collapse 2 or more repeated single tokens / words: "Good. Good. Good. Good." -> "Good."
    cleaned = cleaned.replace(/(?:^|\s)([A-Za-z\u0900-\u097F]+)(?:[.,!?])?(?:\s+\1(?:[.,!?])?)+(?=$|\s|[.,!?])/gi, (match, word) => {
      const lastChar = match.trim().slice(-1);
      return /[.,!?]/.test(lastChar) ? (' ' + word + lastChar) : (' ' + word);
    });

    // 4. Collapse adjacent identical words: "the the" -> "the"
    cleaned = cleaned.replace(/(?:^|\s)([A-Za-z\u0900-\u097F]+)\s+\1(?=$|\s|[.,!?])/gi, ' $1');

    return cleaned.replace(/\s{2,}/g, ' ').trim();
  },

  renderLiveTranscriptInterim(interim) {
    const termArea = document.getElementById('liveStreamingTextArea');
    if (!termArea) return;

    const cleanInterim = this.cleanRepeatedTokens(interim);
    // Retain cumulative text and append colored interim
    const existingFinal = termArea.getAttribute('data-final-text') || '';
    termArea.innerHTML = `${this.escapeHtml(existingFinal)} <span class="streaming-interim">${this.escapeHtml(cleanInterim)}</span>`;
    termArea.scrollTop = termArea.scrollHeight;
  },

  renderLiveTranscriptCumulative(fullText, interim) {
    const termArea = document.getElementById('liveStreamingTextArea');
    const inputArea = document.getElementById('callTranscriptInput');

    const cleanFull = this.cleanRepeatedTokens(fullText);
    const cleanInterim = this.cleanRepeatedTokens(interim);
    const displayText = cleanFull || cleanInterim || '';

    if (inputArea && displayText) {
      inputArea.value = cleanFull || (inputArea.value ? `${inputArea.value} ${cleanInterim}` : cleanInterim);
    }

    if (!termArea) return;
    if (cleanFull) {
      termArea.setAttribute('data-final-text', cleanFull);
    }

    let baseText = cleanFull || termArea.getAttribute('data-final-text') || '';
    let html = this.escapeHtml(baseText);
    if (cleanInterim && cleanInterim !== baseText) {
      html += ` <span class="streaming-interim" style="color: var(--gov-navy, #0284c7); font-weight: 600;">${this.escapeHtml(cleanInterim)}</span>`;
    }
    termArea.innerHTML = html || '<span style="color: var(--text-secondary);">[On-Device AI] आवाज़ सुनी जा रही है...</span>';
    termArea.scrollTop = termArea.scrollHeight;
  },

  updateRiskBanner(data) {
    const currentLang = (window.I18n && window.I18n.currentLang) || 'hi';
    const banner = document.getElementById('callLiveRiskBanner');
    const badge = document.getElementById('riskLevelBadge');
    const catLabel = document.getElementById('scamCategoryLabel');
    const certLabel = document.getElementById('riskCertaintyLabel');
    const explanationEl = document.getElementById('callExplanationText');
    const actionEl = document.getElementById('callActionText');
    const chipsArea = document.getElementById('callSuspiciousChipsArea');
    const chipsList = document.getElementById('callSuspiciousChipsList');

    const level = data.risk_level || 'LOW';

    if (banner) {
      banner.className = `call-risk-banner risk-${level}`;
    }

    if (badge) {
      if (level === 'CRITICAL') {
        badge.textContent = (currentLang === 'en') ? 'CRITICAL HAZARD' : ((currentLang === 'chg') ? 'अत्यंत गंभीर खतरा (CRITICAL)' : 'अत्यंत गंभीर (CRITICAL)');
      } else if (level === 'HIGH') {
        badge.textContent = (currentLang === 'en') ? 'HIGH RISK' : ((currentLang === 'chg') ? 'भारी खतरा (HIGH RISK)' : 'भारी खतरा (HIGH RISK)');
      } else if (level === 'MODERATE') {
        badge.textContent = (currentLang === 'en') ? 'SUSPICIOUS (MODERATE)' : ((currentLang === 'chg') ? 'संदेहास्पद (MODERATE)' : 'संदिग्ध (MODERATE)');
      } else {
        badge.textContent = (currentLang === 'en') ? 'SAFE (LOW RISK)' : ((currentLang === 'chg') ? 'सुरक्षित (LOW RISK)' : 'सुरक्षित (LOW RISK)');
      }
    }

    let cat = data.scam_category;
    let reason = data.reason;
    let action = data.recommended_action;

    if (currentLang === 'en') {
      cat = data.scam_category_en || cat;
      reason = data.reason_en || reason;
      action = data.recommended_action_en || action;
    } else if (currentLang === 'chg') {
      cat = data.scam_category_chg || data.scam_category_hi || cat;
      reason = data.reason_chg || data.reason_hi || reason;
      action = data.recommended_action_chg || data.recommended_action_hi || action;
    } else {
      cat = data.scam_category_hi || cat;
      reason = data.reason_hi || reason;
      action = data.recommended_action_hi || action;
    }

    if (catLabel) {
      catLabel.textContent = cat || ((currentLang === 'en') ? 'Normal Conversation • No Risk' : ((currentLang === 'chg') ? 'सामान्य बातचीत • कोनो खतरा नइ' : 'सामान्य बातचीत • कोई खतरा नहीं'));
    }
    if (certLabel) {
      certLabel.textContent = (currentLang === 'en') ? '100% On-Device Engine' : '100% On-Device Engine';
    }

    if (explanationEl && reason) explanationEl.textContent = reason;
    if (actionEl && action) actionEl.textContent = action;

    // Render suspicious phrases
    const phrases = data.suspicious_phrases || [];
    if (chipsArea && chipsList) {
      if (phrases.length > 0) {
        chipsArea.style.display = 'block';
        chipsList.innerHTML = phrases.map(p => `<span class="suspicious-chip">⚠️ ${this.escapeHtml(p)}</span>`).join('');
      } else {
        chipsArea.style.display = 'none';
      }
    }

    // Update 5-Stage Timeline
    this.updateStageTimeline(data.timeline || data.stages || this.lastStageData || {});
  },

  updateStageTimeline(stageData) {
    const currentLang = (window.I18n && window.I18n.currentLang) || 'hi';
    const activeStages = (stageData && stageData.stages) || [];
    const activeNums = activeStages.map(s => s.stage_num);

    const stageTitles = {
      hi: [
        'भरोसा/पहचान<br><small style="font-weight: normal;">Trust Claim</small>',
        'डर/जल्दबाजी<br><small style="font-weight: normal;">Fear & Urgency</small>',
        'गोपनीय मांग<br><small style="font-weight: normal;">OTP / PIN Request</small>',
        'पैसे ऐंठना<br><small style="font-weight: normal;">Money Demand</small>',
        'डिवाइस हैकिंग<br><small style="font-weight: normal;">APK / AnyDesk</small>'
      ],
      en: [
        'Trust / Identity<br><small style="font-weight: normal;">Authority Claim</small>',
        'Fear & Urgency<br><small style="font-weight: normal;">Panic Pressure</small>',
        'Sensitive Info<br><small style="font-weight: normal;">OTP / PIN Request</small>',
        'Money Demand<br><small style="font-weight: normal;">Financial Transfer</small>',
        'Device Takeover<br><small style="font-weight: normal;">APK / AnyDesk</small>'
      ],
      chg: [
        'भरोसा / पहचान<br><small style="font-weight: normal;">पहचान बताना</small>',
        'डर / हड़बड़ी<br><small style="font-weight: normal;">डर दिखाना</small>',
        'गुप्त मांग<br><small style="font-weight: normal;">OTP / PIN मांगना</small>',
        'पईसा ऐंठना<br><small style="font-weight: normal;">पईसा जमा कराना</small>',
        'मोबाइल हैकिंग<br><small style="font-weight: normal;">ऐप डाउनलोड कराना</small>'
      ]
    };

    const titles = stageTitles[currentLang] || stageTitles.hi;

    for (let i = 1; i <= 5; i++) {
      const box = document.getElementById(`stageBox${i}`);
      if (!box) continue;
      box.classList.remove('active', 'danger');
      box.innerHTML = `<span class="stage-num-chip">${i}</span><div>${titles[i - 1]}</div>`;

      if (activeNums.includes(i)) {
        if (i >= 3) {
          box.classList.add('danger');
        } else {
          box.classList.add('active');
        }
      }
    }

    const percentLabel = document.getElementById('stageProgressPercent');
    if (percentLabel) {
      const pct = (stageData && stageData.progression_percent) || 0;
      if (currentLang === 'en') {
        percentLabel.textContent = `${pct}% Active (${activeStages.length}/5 Stages)`;
      } else {
        percentLabel.textContent = `${pct}% सक्रिय (${activeStages.length}/5 चरण)`;
      }
      if (pct >= 60) {
        percentLabel.style.color = '#dc2626';
      } else if (pct >= 40) {
        percentLabel.style.color = '#d97706';
      } else {
        percentLabel.style.color = 'var(--text-tertiary)';
      }
    }
  },

  updateClaimContradictions(contradictions) {
    const box = document.getElementById('claimEscalationBox');
    const textEl = document.getElementById('claimEscalationText');
    const currentLang = (window.I18n && window.I18n.currentLang) || 'hi';
    if (!box) return;

    if (contradictions && contradictions.length > 0) {
      box.style.display = 'block';
      const prefix = (currentLang === 'en') ? 'Claim Contradiction Detected: ' : ((currentLang === 'chg') ? 'पहचान म बदलाव: ' : 'पहचान में बदलाव: ');
      if (textEl) textEl.textContent = `${prefix}${contradictions.join(' ')}`;
    } else {
      box.style.display = 'none';
    }
  },

  handleWarningInterventions(data) {
    const level = data.risk_level || 'LOW';

    // 1. Silent Warning: Device Vibration (Native Android Bridge or Web API)
    if (level === 'CRITICAL') {
      if (window.SurakshaNative && window.SurakshaNative.vibrate) {
        window.SurakshaNative.vibrate(JSON.stringify([200, 100, 200, 100, 300]));
      } else if (navigator.vibrate) {
        navigator.vibrate([200, 100, 200, 100, 300]);
      }
    } else if (level === 'HIGH') {
      if (window.SurakshaNative && window.SurakshaNative.vibrate) {
        window.SurakshaNative.vibrate(JSON.stringify([150, 100, 150]));
      } else if (navigator.vibrate) {
        navigator.vibrate([150, 100, 150]);
      }
    }

    // 2. Audio Spoken Warning (Offline Pre-synthesised Audio with TTS Fallback)
    if (this.audioWarningEnabled && (level === 'CRITICAL' || level === 'HIGH')) {
      const currentLang = (window.I18n && window.I18n.currentLang) || 'hi';
      const catList = (data.matched_categories || []).join(',');
      const dedupeKey = `${level}:${catList}:${currentLang}`;
      if (dedupeKey !== this.lastSpokenWarning) {
        this.lastSpokenWarning = dedupeKey;
        this.playAudioAlert(data, currentLang);
      }
    }

    // 3. Critical Warning Screen
    if (level === 'CRITICAL') {
      this.showCriticalWarningModal(data);
    }
  },

  showCriticalWarningModal(data) {
    const modal = document.getElementById('criticalWarningModal');
    const subheader = document.getElementById('critWarningSubheader');
    const expl = document.getElementById('critWarningExplanation');
    const currentLang = (window.I18n && window.I18n.currentLang) || 'hi';

    let cat = data.scam_category;
    let reason = data.reason;
    if (currentLang === 'en') {
      cat = data.scam_category_en || cat;
      reason = data.reason_en || reason;
    } else if (currentLang === 'chg') {
      cat = data.scam_category_chg || data.scam_category_hi || cat;
      reason = data.reason_chg || data.reason_hi || reason;
    } else {
      cat = data.scam_category_hi || cat;
      reason = data.reason_hi || reason;
    }

    if (modal) {
      if (subheader && cat) subheader.textContent = cat;
      if (expl && reason) expl.textContent = reason;
      modal.style.display = 'flex';
    }
  },

  playAudioAlert(data, lang) {
    if (!this.audioWarningEnabled) return;

    const currentLang = lang || (window.I18n && window.I18n.currentLang) || 'hi';
    const targetLang = (currentLang === 'en') ? 'en' : ((currentLang === 'chg') ? 'chg' : 'hi');

    // Resolve primary category
    const categories = (data && data.matched_categories) || [];
    const ruleFlags = (data && data.rule_flags) || {};
    let catKey = 'upi_pin';
    if (categories.includes('upi_pin_fraud')) {
      catKey = 'upi_pin';
    } else if (categories.includes('otp_fraud') || ruleFlags.explicit_otp_demand) {
      catKey = 'otp';
    } else if (categories.includes('digital_arrest') || categories.includes('police_govt_impersonation') || ruleFlags.digital_arrest) {
      catKey = 'police';
    } else if (categories.includes('remote_access') || ruleFlags.remote_access_apk) {
      catKey = 'remote_access';
    } else if (categories.includes('bank_impersonation') || ruleFlags.fake_kyc) {
      catKey = 'bank_kyc';
    } else if (categories.includes('financial_extortion') || categories.includes('utility_electricity') || categories.includes('lottery_subsidy') || categories.includes('courier_customs')) {
      catKey = 'extortion';
    } else {
      catKey = 'extortion';
    }

    const alertFile = `/assets/alerts/alert_${catKey}_${targetLang}.wav`;

    let fallbackText = "";
    if (targetLang === 'en') {
      fallbackText = (data && data.audio_warning_en) || "Warning! Never share your confidential OTP or UPI PIN.";
    } else if (targetLang === 'chg') {
      fallbackText = (data && (data.audio_warning_chg || data.audio_warning_hi)) || "सचेत रहव! ककरो ले अपन OTP या UPI PIN झन बतावव।";
    } else {
      fallbackText = (data && data.audio_warning_hi) || "सावधान! किसी को भी अपना OTP या UPI PIN न बताएं।";
    }

    if (this.currentAudioPlayer) {
      try {
        this.currentAudioPlayer.pause();
        this.currentAudioPlayer = null;
      } catch (e) {}
    }

    this.isPlayingAlert = true;
    const alertAudio = new Audio(alertFile);
    this.currentAudioPlayer = alertAudio;

    alertAudio.onended = () => {
      this.isPlayingAlert = false;
      this.currentAudioPlayer = null;
    };

    alertAudio.onerror = (e) => {
      console.warn("Offline alert audio file failed or missing, falling back to Web Speech API:", alertFile, e);
      this.isPlayingAlert = false;
      this.currentAudioPlayer = null;
      this.speakWarning(fallbackText, targetLang === 'en' ? 'en' : 'hi');
    };

    alertAudio.play().catch((err) => {
      console.warn("Audio autoplay blocked or failed, falling back to Web Speech:", err);
      this.isPlayingAlert = false;
      this.currentAudioPlayer = null;
      this.speakWarning(fallbackText, targetLang === 'en' ? 'en' : 'hi');
    });
  },

  speakWarning(text, lang = "hi") {
    if (!('speechSynthesis' in window)) return;

    try {
      window.speechSynthesis.cancel(); // Stop any pending speech
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = (lang === 'en') ? 'en-IN' : 'hi-IN';
      utter.rate = 0.95; // Slightly slower for clarity
      utter.pitch = 1.0;

      // Select matching regional voice if available
      const voices = window.speechSynthesis.getVoices();
      if (voices && voices.length > 0) {
        const matchVoice = voices.find(v => v.lang && v.lang.toLowerCase().startsWith(utter.lang.toLowerCase()));
        if (matchVoice) utter.voice = matchVoice;
      }

      window.speechSynthesis.speak(utter);
    } catch (e) {
      console.warn('Speech synthesis warning notice:', e);
    }
  },

  triggerFamilyAlert() {
    const msg = encodeURIComponent("आपातकालीन अलर्ट: मुझे एक संदिग्ध कॉल आई है जिसमें OTP/UPI PIN मांगा जा रहा है। मैंने कॉल काट दी है। कृपया सतर्क रहें।");
    window.location.href = `sms:?body=${msg}`;
  },

  stopLiveListening() {
    this.isListening = false;
    this.updateMicPermissionPill();

    const pulseDot = document.getElementById('livePulseDot');
    if (pulseDot) pulseDot.classList.remove('active');
    const statusText = document.getElementById('liveStatusText');
    if (statusText) statusText.textContent = 'लाइव बातचीत (माइक बंद)';

    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }

    if (this.chunkIntervalTimer) {
      clearInterval(this.chunkIntervalTimer);
      this.chunkIntervalTimer = null;
    }

    // Stop native Android CallGuardianService foreground service if running inside APK
    if (window.SurakshaNative && window.SurakshaNative.stopCallGuardian) {
      window.SurakshaNative.stopCallGuardian();
    }

    // Stop any playing alert audio
    if (this.currentAudioPlayer) {
      try {
        this.currentAudioPlayer.pause();
        this.currentAudioPlayer = null;
      } catch (e) {}
    }
    this.isPlayingAlert = false;

    // Disconnect and clean up AudioWorklet and AudioContext
    if (this.audioWorkletNode) {
      try { this.audioWorkletNode.disconnect(); } catch (e) {}
      this.audioWorkletNode = null;
    }
    if (this.mediaStreamSource) {
      try { this.mediaStreamSource.disconnect(); } catch (e) {}
      this.mediaStreamSource = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      try { this.audioContext.close(); } catch (e) {}
      this.audioContext = null;
    }

    // Close WebSocket and notify backend
    if (this.webSocket) {
      if (this.webSocket.readyState === WebSocket.OPEN) {
        try {
          this.webSocket.send(JSON.stringify({
            type: 'stop',
            session_id: this.streamSessionId
          }));
        } catch (e) {}
      }
      try { this.webSocket.close(); } catch (e) {}
      this.webSocket = null;
    }
    this.webSocketConnected = false;

    // Release and stop all audio tracks immediately
    if (this.mediaStream) {
      try {
        this.mediaStream.getTracks().forEach((track) => {
          track.stop();
          track.enabled = false;
        });
      } catch (e) {}
      this.mediaStream = null;
    }

    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try { this.mediaRecorder.stop(); } catch (e) {}
      this.mediaRecorder = null;
    }

    if (this.speechRecognizer) {
      try {
        this.speechRecognizer.abort();
        this.speechRecognizer.stop();
      } catch (e) {}
      this.speechRecognizer = null;
    }

    if (this.durationTimer) {
      clearInterval(this.durationTimer);
      this.durationTimer = null;
    }

    const btn = document.getElementById('btnLiveCallListen');
    const btnText = document.getElementById('liveListenBtnText');
    const vadPill = document.getElementById('vadStatusPill');

    if (btn) {
      btn.classList.remove('listening');
      btn.classList.add('idle');
    }
    if (btnText) btnText.textContent = 'कॉल सुनना शुरू करें (Start Listening)';
    if (vadPill) {
      vadPill.textContent = '⚪ VAD: माइक बंद (Inactive)';
      vadPill.classList.remove('active');
    }

    // Call backend session stop HTTP as final sync
    if (this.streamSessionId) {
      fetch('/api/calls/session-stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: this.streamSessionId })
      }).then(res => res.json()).then(data => {
        if (data && (data.final_transcript || data.text || data.transcript)) {
          const rawTxt = data.final_transcript || data.text || data.transcript;
          const finalTxt = this.cleanRepeatedTokens(rawTxt);
          const transcriptInput = document.getElementById('callTranscriptInput');
          if (transcriptInput && finalTxt) {
            transcriptInput.value = finalTxt;
          }
          const termArea = document.getElementById('liveStreamingTextArea');
          if (termArea && finalTxt) {
            termArea.setAttribute('data-final-text', finalTxt);
            termArea.innerHTML = this.escapeHtml(finalTxt);
          }
          if (finalTxt) {
            this.evaluateLiveText(finalTxt);
          }
        }
      }).catch(err => console.debug('Stop notice:', err));
    }
  },

  async simulateScenarioRun(text, lang = "hi") {
    // Stops active listening if any
    if (this.isListening) this.stopLiveListening();

    const termArea = document.getElementById('liveStreamingTextArea');
    if (termArea) {
      termArea.innerHTML = `<span style="color: #38bdf8;">[Scenario Simulation: ${this.escapeHtml(text)}]</span>`;
    }

    const currentUiLang = (window.I18n && window.I18n.currentLang) || lang || 'hi';

    // Post to unified detect endpoint
    const formData = new FormData();
    formData.append('transcript', text);
    formData.append('language', currentUiLang);
    formData.append('call_lang', lang || currentUiLang);
    formData.append('session_id', `scenario_${Date.now()}`);

    try {
      const resp = await fetch('/api/detect/call', {
        method: 'POST',
        body: formData
      });
      const data = await resp.json();
      data.force_update = true;
      this.lastAnalysisData = data;
      if (data.stages || data.timeline) {
        this.lastStageData = data.stages || data.timeline;
      }
      this.handleStreamingResponse(data);
      this.renderFullVerdictBox(data);
    } catch (e) {
      console.error('Scenario run error:', e);
    }
  },

  async evaluateLiveText(text) {
    // Quick evaluate live interim text against backend
    const langSelect = document.getElementById('callAudioLang');
    const lang = (langSelect && langSelect.value) || 'auto';
    const currentUiLang = (window.I18n && window.I18n.currentLang) || 'hi';

    const formData = new FormData();
    formData.append('transcript', text);
    formData.append('language', currentUiLang);
    formData.append('call_lang', lang);
    formData.append('session_id', this.streamSessionId || `live_${Date.now()}`);

    try {
      const resp = await fetch('/api/detect/call', { method: 'POST', body: formData });
      const data = await resp.json();
      this.lastAnalysisData = data;
      if (data.stages || data.timeline) {
        this.lastStageData = data.stages || data.timeline;
      }
      this.handleStreamingResponse(data);
    } catch (e) {
      console.debug('Live evaluate notice:', e);
    }
  },

  async loadAudioSample(key) {
    const url = this.audioSamples[key];
    if (!url) return;

    this.showStatus('⏳ सैंपल ऑडियो लोड हो रहा है...', 'info');
    try {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error('Audio fetch failed');
      const blob = await resp.blob();
      const file = new File([blob], `${key}_sample.wav`, { type: 'audio/wav' });
      this.activeAudioFile = file;

      const player = document.getElementById('callAudioPlayer');
      if (player) {
        player.src = URL.createObjectURL(blob);
        player.style.display = 'block';
      }

      this.showStatus(`✅ ऑडियो लोड हुआ (${file.name})। ऑफलाइन Whisper Medium AI से विश्लेषण शुरू हो रहा है...`, 'info');
      await this.analyzeCall();
    } catch (e) {
      console.error('Audio load error:', e);
      this.showStatus('ऑडियो लोड करने में त्रुटि आई', 'error');
    }
  },

  async analyzeCall() {
    const audioInput = document.getElementById('callAudioFile');
    const transcriptInput = document.getElementById('callTranscriptInput');
    const langSelect = document.getElementById('callAudioLang');

    const file = this.activeAudioFile || (audioInput && audioInput.files ? audioInput.files[0] : null);
    const text = transcriptInput ? transcriptInput.value.trim() : '';

    if (!file && !text) {
      if (window.App) window.App.showToast('कृपया कॉल रिकॉर्डिंग ऑडियो अपलोड करें या बातचीत पेस्ट करें');
      return;
    }

    const currentUiLang = (window.I18n && window.I18n.currentLang) || 'hi';
    const formData = new FormData();
    if (file) {
      formData.append('audio', file);
      this.showStatus('🎙️ ऑफलाइन Whisper Medium AI मॉडल द्वारा आवाज़ से टेक्स्ट निकाला जा रहा है...', 'info');
    }
    if (text) formData.append('transcript', text);
    formData.append('language', currentUiLang);
    formData.append('call_lang', (langSelect && langSelect.value) || 'auto');
    formData.append('session_id', `manual_${Date.now()}`);

    const btn = document.getElementById('btnAnalyzeCall');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'जांच हो रही है...';
    }

    try {
      const res = await fetch('/api/detect/call', { method: 'POST', body: formData });
      const data = await res.json();
      data.force_update = true;
      this.lastAnalysisData = data;
      if (data.stages || data.timeline) {
        this.lastStageData = data.stages || data.timeline;
      }

      const rawExtracted = data.text || data.transcript || '';
      const extractedText = this.cleanRepeatedTokens(rawExtracted);
      data.text = extractedText;
      data.transcript = extractedText;

      const transcriptInput = document.getElementById('callTranscriptInput');
      if (transcriptInput && extractedText) {
        transcriptInput.value = extractedText;
        transcriptInput.style.border = '2px solid #059669';
        transcriptInput.style.boxShadow = '0 0 10px rgba(5, 150, 105, 0.2)';
        setTimeout(() => {
          transcriptInput.style.border = '';
          transcriptInput.style.boxShadow = '';
        }, 4000);
      }

      this.handleStreamingResponse(data);
      this.renderFullVerdictBox(data);

      if (extractedText) {
        const wordCount = extractedText.trim().split(/\s+/).length;
        this.showStatus(`✅ आवाज़ से बातचीत सफलतापूर्वक निकाली गई (${wordCount} शब्द) • ${data.transcription_notice || 'Whisper Medium 100% On-Device Engine'}`, 'success');
        // Clear activeAudioFile once transcribed so subsequent Analyze clicks instantly re-evaluate the text
        this.activeAudioFile = null;
      } else {
        this.showStatus('⚠️ आवाज़ से कोई स्पष्ट बातचीत नहीं मिली। कृपया साफ़ आवाज़ की रिकॉर्डिंग अपलोड करें या बातचीत पेस्ट करें।', 'error');
      }

      // Smooth scroll to extracted transcript and verdict
      if (transcriptInput) {
        transcriptInput.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    } catch (err) {
      console.error('Call analysis error:', err);
      this.showStatus('विश्लेषण में त्रुटि आई। कृपया पुनः प्रयास करें।', 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'कॉल का सच जांचें';
      }
    }
  },

  renderFullVerdictBox(data) {
    const vBox = document.getElementById('callVerdictBox');
    if (!vBox) return;

    const currentLang = (window.I18n && window.I18n.currentLang) || 'hi';
    const isDanger = data.risk_level === 'CRITICAL' || data.risk_level === 'HIGH' || data.verdict === 'likely_scam';
    const isSafe = data.risk_level === 'LOW' && data.verdict === 'genuine';

    vBox.className = 'verdict-box show';
    vBox.classList.add(isDanger ? 'danger' : (isSafe ? 'safe' : 'warning'));

    // Resolve localized script_meta
    let scriptMeta = data.script_meta;
    if (data.script_meta_map) {
      scriptMeta = data.script_meta_map[currentLang] || data.script_meta_map.hi || data.script_meta_map.en;
    }

    let scriptHtml = '';
    const advicePrefix = (currentLang === 'en') ? 'Advice:' : 'सलाह:';
    if (scriptMeta) {
      scriptHtml = `
        <div style="background: rgba(220, 38, 38, 0.08); border-left: 4px solid #dc2626; padding: var(--space-2) var(--space-3); border-radius: 4px; margin-bottom: var(--space-3);">
          <div style="font-weight: 800; font-size: var(--text-sm); color: #991b1b;">${this.escapeHtml(scriptMeta.title)}</div>
          <div style="font-size: var(--text-xs); color: #7f1d1d; margin-top: 2px;">${this.escapeHtml(scriptMeta.danger_banner)}</div>
          <div style="font-size: var(--text-xs); color: var(--text-primary); margin-top: 4px; font-weight: 600;">${advicePrefix} ${this.escapeHtml(scriptMeta.action_advice)}</div>
        </div>
      `;
    }

    // Localized badge text
    let badgeText = '';
    if (isDanger) {
      badgeText = (currentLang === 'en') ? '🚨 Likely Scam Call (High Risk)' : ((currentLang === 'chg') ? '🚨 ठगी के भारी खतरा हे! (Likely Scam)' : '🚨 संभावित स्कैम कॉल (Likely Scam)');
    } else if (isSafe) {
      badgeText = (currentLang === 'en') ? '✅ Looks Genuine (Safe)' : ((currentLang === 'chg') ? '✅ सीधा साधा बातचीत (Genuine)' : '✅ सुरक्षित बातचीत (Genuine)');
    } else {
      badgeText = (currentLang === 'en') ? '⚠️ Suspicious Call (Moderate Risk)' : ((currentLang === 'chg') ? '⚠️ संदेहास्पद बातचीत (Suspicious)' : '⚠️ संदिग्ध बातचीत (Suspicious)');
    }

    const accuracyLabel = (currentLang === 'en') ? 'Confidence:' : 'सटीकता:';
    const explanationHeader = (currentLang === 'en') ? 'Reason & Explanation:' : ((currentLang === 'chg') ? 'सरल व्याख्या:' : 'सरल व्याख्या (Explanation):');
    const actionHeader = (currentLang === 'en') ? 'Recommended Action:' : ((currentLang === 'chg') ? 'सलाह (Action):' : 'सलाह (Action):');
    const call1930BtnText = (currentLang === 'en') ? 'Call 1930 Helpline Now' : ((currentLang === 'chg') ? '1930 म तुरंत फोन लगावा' : '1930 पर तुरंत कॉल करें');
    const speakBtnText = (currentLang === 'en') ? 'Listen to Voice Warning' : ((currentLang === 'chg') ? 'चेतावनी सुनावव' : 'बोलकर सुनाएं');

    // Localized reason and action
    let explanationText = data.explanation || data.reason || '';
    let actionText = data.recommended_action || '';
    if (currentLang === 'en') {
      explanationText = data.reason_en || explanationText;
      actionText = data.recommended_action_en || actionText || 'Stay vigilant. Never share private verification codes with anyone.';
    } else if (currentLang === 'chg') {
      explanationText = data.reason_chg || data.reason_hi || explanationText;
      actionText = data.recommended_action_chg || data.recommended_action_hi || actionText || 'सचेत रहव! ककरो ले अपन गुप्त जानकारी कभू शेयर झन करव।';
    } else {
      explanationText = data.reason_hi || explanationText;
      actionText = data.recommended_action_hi || actionText || 'सतर्क रहें। किसी अनजान व्यक्ति के साथ गुप्त जानकारी कभी साझा न करें।';
    }

    const ttsText = (currentLang === 'en') ? (data.audio_warning_en || explanationText) : (data.audio_warning_hi || explanationText);

    // Synchronize the single unified explanation and action elements
    const explEl = document.getElementById('callExplanationText');
    const actEl = document.getElementById('callActionText');
    if (explEl) explEl.textContent = explanationText;
    if (actEl) actEl.textContent = actionText;

    const certLabel = document.getElementById('riskCertaintyLabel');
    if (certLabel) {
      certLabel.textContent = `${accuracyLabel} ${data.confidence_percent || 95}% • 100% On-Device`;
    }

    // Display localized script danger advisory banner inside explanation box
    const scriptBanner = document.getElementById('callScriptBannerContainer');
    if (scriptBanner) {
      if (scriptHtml) {
        scriptBanner.innerHTML = scriptHtml;
        scriptBanner.style.display = 'block';
      } else {
        scriptBanner.innerHTML = '';
        scriptBanner.style.display = 'none';
      }
    }

    // Keep legacy callVerdictBox hidden to avoid duplicate card rendering
    vBox.style.display = 'none';
    vBox.innerHTML = '';
  },

  onLanguageChanged(newLang) {
    const lang = newLang || (window.I18n && window.I18n.currentLang) || 'hi';
    const callAudioLang = document.getElementById('callAudioLang');
    if (callAudioLang && callAudioLang.value !== 'auto' && callAudioLang.value !== lang) {
      callAudioLang.value = lang;
    }

    // 1. Re-render timeline stage labels
    this.updateStageTimeline(this.lastStageData || {});

    // 2. If we have active analysis data, re-render risk banner, verdict box, and critical modal
    if (this.lastAnalysisData) {
      this.updateRiskBanner(this.lastAnalysisData);
      this.renderFullVerdictBox(this.lastAnalysisData);
      const modal = document.getElementById('criticalWarningModal');
      if (modal && modal.style.display !== 'none') {
        this.showCriticalWarningModal(this.lastAnalysisData);
      }
    } else {
      // Default low risk banner localized
      const defaultData = {
        risk_level: 'LOW',
        scam_category: (lang === 'en') ? 'Normal Conversation • No Threat' : ((lang === 'chg') ? 'सामान्य बातचीत • कोनो खतरा नइ' : 'सामान्य बातचीत • कोई खतरा नहीं'),
        reason: (lang === 'en') ? 'No financial fraud or suspicious indicators found in conversation.' : ((lang === 'chg') ? 'गोठ-बात म कोनो ठगी या संदेहास्पद संकेत नइ मिले हे।' : 'बातचीत में कोई वित्तीय धोखाधड़ी या संदिग्ध संकेत नहीं मिले हैं।'),
        recommended_action: (lang === 'en') ? 'Stay vigilant. Never share secret credentials with unknown callers.' : ((lang === 'chg') ? 'सचेत रहव। अनजान मनखे ले अपन गुप्त जानकारी कभू शेयर झन करव।' : 'सतर्क रहें। किसी अनजान व्यक्ति के साथ गुप्त जानकारी कभी साझा न करें।')
      };
      this.updateRiskBanner(defaultData);
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

  resetAll() {
    this.stopLiveListening();
    const transcriptInput = document.getElementById('callTranscriptInput');
    const audioInput = document.getElementById('callAudioFile');
    const player = document.getElementById('callAudioPlayer');
    const vBox = document.getElementById('callVerdictBox');
    const termArea = document.getElementById('liveStreamingTextArea');

    if (transcriptInput) transcriptInput.value = '';
    if (audioInput) audioInput.value = '';
    this.activeAudioFile = null;

    if (player) {
      player.pause();
      player.src = '';
      player.style.display = 'none';
    }
    this.hideStatus();
    const scriptBanner = document.getElementById('callScriptBannerContainer');
    if (scriptBanner) {
      scriptBanner.innerHTML = '';
      scriptBanner.style.display = 'none';
    }
    if (vBox) vBox.classList.remove('show', 'danger', 'warning', 'safe');
    if (termArea) termArea.innerHTML = '<span style="color: #64748b;">कॉल सुनना शुरू करने के लिए ऊपर \'कॉल सुनना शुरू करें\' बटन दबाएं, या नीचे दिया गया कोई सैंपल चलाएं...</span>';

    // Reset risk banner to default Low
    this.updateRiskBanner({
      risk_level: 'LOW',
      scam_category: 'सामान्य बातचीत • कोई खतरा नहीं',
      reason: 'बातचीत में कोई वित्तीय धोखाधड़ी या संदिग्ध संकेत नहीं मिले हैं।',
      recommended_action: 'सतर्क रहें। किसी अनजान व्यक्ति के साथ गुप्त जानकारी कभी साझा न करें।'
    });
    this.updateClaimContradictions([]);
  },

  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
};

window.CallDetector = CallDetector;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  CallDetector.init();
});

// Resume AudioContext if browser tab is foregrounded after suspension
document.addEventListener('visibilitychange', () => {
  if (window.CallDetector && window.CallDetector.isListening && window.CallDetector.audioContext) {
    if (document.visibilityState === 'visible' && window.CallDetector.audioContext.state === 'suspended') {
      window.CallDetector.audioContext.resume().catch(() => {});
    }
  }
});
