// Jan Suraksha - Offline Voice Speech-to-Text Engine (Vosk WASM / Native Bridge / Mock Interface)
// Strict Zero-Cloud, Zero-Upload, In-Memory Audio Processing.

(function (global) {
  'use strict';

  const VoiceEngine = {
    isListening: false,
    currentModelLang: null,
    voskModel: null,
    recognizer: null,
    mediaStream: null,
    audioContext: null,
    recognizerNode: null,
    silenceTimer: null,
    speechDetected: false,
    mockTranscript: null,
    lastRecognizedText: '',

    callbacks: {
      onListening: null,
      onTranscript: null,
      onPartial: null,
      onError: null,
      onEnd: null,
      onProgress: null
    },

    isSupported() {
      // 1. Mock mode always supported
      if (this.mockTranscript !== null) return true;

      // 2. Android Native Bridge support
      if (window.SurakshaNative && typeof window.SurakshaNative.hasNativeSpeechRecognizer === 'function' && window.SurakshaNative.hasNativeSpeechRecognizer()) {
        return true;
      }

      // 3. Web getUserMedia & WebAudio support for in-browser Vosk WASM
      const hasMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
      const hasAudioCtx = !!(window.AudioContext || window.webkitAudioContext);
      return hasMedia && hasAudioCtx;
    },

    /**
     * Testing hook: Injects a mock transcript that will be triggered when start() is called.
     */
    setMockTranscript(text) {
      this.mockTranscript = text;
    },

    /**
     * Testing hook: Immediately triggers a transcript callback.
     */
    mockTrigger(text) {
      this.lastRecognizedText = text || '';
      if (this.callbacks.onTranscript) {
        this.callbacks.onTranscript(this.lastRecognizedText);
      }
      this.stop();
    },

    /**
     * Lazy-loads the offline Vosk WASM model.
     * Chhattisgarhi has no dedicated model, so it uses the Hindi model as specified.
     */
    async loadVoskModel(lang = 'hi', onProgress) {
      const targetLang = (lang === 'en') ? 'en' : 'hi';
      if (this.voskModel && this.currentModelLang === targetLang) {
        return this.voskModel;
      }

      // Ensure vendor vosk.js is loaded
      if (typeof Vosk === 'undefined') {
        if (onProgress) onProgress(15, 'Loading Speech Engine...');
        await this.loadVendorScript('/js/vendor/vosk.js');
      }

      const modelUrl = targetLang === 'en' 
        ? '/assets/models/vosk-model-en.tar.gz' 
        : '/assets/models/vosk-model-hi.tar.gz';

      if (onProgress) onProgress(35, `Loading Offline ${targetLang.toUpperCase()} Model...`);

      try {
        if (typeof Vosk !== 'undefined' && typeof Vosk.createModel === 'function') {
          this.voskModel = await Vosk.createModel(modelUrl);
          this.currentModelLang = targetLang;
          if (onProgress) onProgress(100, 'Model Ready');
          return this.voskModel;
        } else {
          throw new Error('Vosk library could not be initialized');
        }
      } catch (err) {
        console.warn('[VoiceEngine] Could not initialize Vosk WASM model:', err);
        throw err;
      }
    },

    loadVendorScript(src) {
      return new Promise((resolve, reject) => {
        if (document.querySelector(`script[src="${src}"]`)) {
          resolve();
          return;
        }
        const script = document.createElement('script');
        script.src = src;
        script.onload = () => resolve();
        script.onerror = (e) => reject(new Error(`Failed to load script ${src}`));
        document.head.appendChild(script);
      });
    },

    async start(options = {}) {
      if (this.isListening) {
        this.stop();
      }

      const lang = options.lang || (window.I18n ? window.I18n.currentLang : 'hi') || 'hi';
      this.callbacks.onListening = options.onListening || null;
      this.callbacks.onTranscript = options.onTranscript || null;
      this.callbacks.onPartial = options.onPartial || null;
      this.callbacks.onError = options.onError || null;
      this.callbacks.onEnd = options.onEnd || null;
      this.callbacks.onProgress = options.onProgress || null;

      this.isListening = true;
      this.speechDetected = false;
      this.lastRecognizedText = '';

      // Test Mock Bypass
      if (this.mockTranscript !== null) {
        const text = this.mockTranscript;
        if (this.callbacks.onListening) this.callbacks.onListening();
        // Simulate speech recognition latency
        setTimeout(() => {
          if (!this.isListening) return;
          this.lastRecognizedText = text;
          if (this.callbacks.onPartial) this.callbacks.onPartial(text);
          setTimeout(() => {
            if (!this.isListening) return;
            if (this.callbacks.onTranscript) this.callbacks.onTranscript(text);
            this.stop('mock_finished');
          }, 300);
        }, 200);
        return;
      }

      // Check mic permissions & hardware
      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          video: false,
          audio: {
            channelCount: 1,
            sampleRate: 16000,
            echoCancellation: true,
            noiseSuppression: true
          }
        });
      } catch (permErr) {
        this.isListening = false;
        console.warn('[VoiceEngine] Microphone access denied or error:', permErr);
        if (this.callbacks.onError) {
          this.callbacks.onError({
            code: 'permission_denied',
            message: 'Microphone permission denied',
            originalError: permErr
          });
        }
        return;
      }

      // Notify UI that mic is active
      if (this.callbacks.onListening) {
        this.callbacks.onListening();
      }

      // Setup 8-second safety silence timer
      this.resetSilenceTimer(8000);

      // Attempt Vosk WASM speech recognition pipeline
      try {
        const model = await this.loadVoskModel(lang, this.callbacks.onProgress);

        // Build restricted grammar from intent phrase lists
        let grammarStr = undefined;
        if (window.VoiceMatcher && window.VoiceMatcher.intentsData && window.VoiceMatcher.intentsData.vosk_grammar_tokens) {
          grammarStr = JSON.stringify(window.VoiceMatcher.intentsData.vosk_grammar_tokens);
        }

        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        this.audioContext = new AudioCtx({ sampleRate: 16000 });

        if (grammarStr) {
          try {
            this.recognizer = new model.KaldiRecognizer(16000, grammarStr);
          } catch (gErr) {
            this.recognizer = new model.KaldiRecognizer(16000);
          }
        } else {
          this.recognizer = new model.KaldiRecognizer(16000);
        }

        this.recognizer.on('result', (msg) => {
          const text = msg.result && msg.result.text ? msg.result.text.trim() : '';
          if (text) {
            this.lastRecognizedText = text;
            if (this.callbacks.onTranscript) {
              this.callbacks.onTranscript(text);
            }
            this.stop('final_result');
          }
        });

        this.recognizer.on('partialresult', (msg) => {
          const partial = msg.result && msg.result.partial ? msg.result.partial.trim() : '';
          if (partial) {
            this.lastRecognizedText = partial;
            this.speechDetected = true;
            this.resetSilenceTimer(2500); // User is speaking, allow 2.5s pause after speech
            if (this.callbacks.onPartial) {
              this.callbacks.onPartial(partial);
            }
          }
        });

        // ScriptProcessor Node for streaming raw audio samples into Vosk
        this.recognizerNode = this.audioContext.createScriptProcessor(4096, 1, 1);
        this.recognizerNode.onaudioprocess = (event) => {
          if (!this.isListening) return;

          const inputBuffer = event.inputBuffer;
          const channelData = inputBuffer.getChannelData(0);

          // Simple in-memory RMS VAD to detect speech start
          let sum = 0;
          for (let i = 0; i < channelData.length; i++) {
            sum += channelData[i] * channelData[i];
          }
          const rms = Math.sqrt(sum / channelData.length);

          if (rms > 0.02) {
            if (!this.speechDetected) {
              this.speechDetected = true;
            }
            this.resetSilenceTimer(2500);
          }

          if (this.recognizer) {
            try {
              this.recognizer.acceptWaveform(inputBuffer);
            } catch (recErr) {
              console.warn('[VoiceEngine] acceptWaveform notice:', recErr);
            }
          }
        };

        const source = this.audioContext.createMediaStreamSource(this.mediaStream);
        source.connect(this.recognizerNode);

        // Connect through silent gain to keep audio ticks running
        const silentGain = this.audioContext.createGain();
        silentGain.gain.value = 0.0;
        this.recognizerNode.connect(silentGain);
        silentGain.connect(this.audioContext.destination);

      } catch (engineErr) {
        console.warn('[VoiceEngine] Vosk engine failure, falling back to simulated listener:', engineErr);
        // If Vosk fails to load or compile on an ultra low-end browser, keep listening active
        // so timeout or fallback UI triggers smoothly without unhandled error.
        this.resetSilenceTimer(4000);
      }
    },

    resetSilenceTimer(durationMs) {
      if (this.silenceTimer) {
        clearTimeout(this.silenceTimer);
      }
      this.silenceTimer = setTimeout(() => {
        console.log('[VoiceEngine] Silence / speech timeout elapsed');
        if (this.lastRecognizedText && this.callbacks.onTranscript) {
          this.callbacks.onTranscript(this.lastRecognizedText);
        }
        this.stop('timeout');
      }, durationMs);
    },

    stop(reason = 'user_stopped') {
      if (!this.isListening) return;
      this.isListening = false;

      if (this.silenceTimer) {
        clearTimeout(this.silenceTimer);
        this.silenceTimer = null;
      }

      // 1. Release MediaStream tracks (microphone hardware)
      if (this.mediaStream) {
        try {
          this.mediaStream.getTracks().forEach(track => track.stop());
        } catch (e) {}
        this.mediaStream = null;
      }

      // 2. Disconnect and close AudioContext
      if (this.recognizerNode) {
        try { this.recognizerNode.disconnect(); } catch (e) {}
        this.recognizerNode = null;
      }
      if (this.audioContext && this.audioContext.state !== 'closed') {
        try { this.audioContext.close(); } catch (e) {}
        this.audioContext = null;
      }

      // 3. Remove recognizer instance
      if (this.recognizer) {
        try { this.recognizer.remove(); } catch (e) {}
        this.recognizer = null;
      }

      // 4. Trigger onEnd callback
      if (this.callbacks.onEnd) {
        this.callbacks.onEnd({
          reason: reason,
          lastText: this.lastRecognizedText
        });
      }
    }
  };

  global.VoiceEngine = VoiceEngine;
})(typeof window !== 'undefined' ? window : globalThis);
