// Jan Suraksha - Voice-First Helper Manager
// Offline Voice Navigation, Intent Dispatching, Spoken Audio Prompts & Paste Workflow

(function (global) {
  'use strict';

  const VoiceHelper = {
    initialized: false,
    isFlowActive: false,
    playbackToken: 0,
    retryCount: 0,
    currentIntentResult: null,
    audioPlayer: null,

    init() {
      if (this.initialized) return;
      this.initialized = true;

      if (window.VoiceMatcher) {
        window.VoiceMatcher.init();
      }

      this.bindUiElements();
      this.bindPasteButton();
    },

    bindUiElements() {
      // 1. Home screen big mic button
      const homeMicBtn = document.getElementById('homeVoiceMicBtn');
      if (homeMicBtn) {
        homeMicBtn.addEventListener('click', () => this.startListeningFlow());
      }

      // 2. Floating voice mic button
      const floatingMicBtn = document.getElementById('floatingVoiceBtn');
      if (floatingMicBtn) {
        floatingMicBtn.addEventListener('click', () => this.startListeningFlow());
      }

      // 3. Modal close and try again buttons
      const btnClose = document.getElementById('btnVoiceModalClose');
      if (btnClose) {
        btnClose.addEventListener('click', () => this.closeModal());
      }

      const btnTryAgain = document.getElementById('btnVoiceTryAgain');
      if (btnTryAgain) {
        btnTryAgain.addEventListener('click', () => this.startListeningFlow());
      }

      const modalOverlay = document.getElementById('voiceModalOverlay');
      if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
          if (e.target === modalOverlay) this.closeModal();
        });
      }

      // 4. Fallback 4 Big Action Buttons
      const btnFbMsg = document.getElementById('voiceFallbackMsg');
      if (btnFbMsg) {
        btnFbMsg.addEventListener('click', () => {
          this.closeModal();
          this.dispatchIntent({
            intent: 'whatsapp_or_sms_message',
            subType: 'message',
            targetView: 'check',
            targetSubtab: 'subtab-sms'
          });
        });
      }

      const btnFbCall = document.getElementById('voiceFallbackCall');
      if (btnFbCall) {
        btnFbCall.addEventListener('click', () => {
          this.closeModal();
          this.dispatchIntent({
            intent: 'phone_call',
            targetView: 'check',
            targetSubtab: 'subtab-call'
          });
        });
      }

      const btnFbQr = document.getElementById('voiceFallbackQr');
      if (btnFbQr) {
        btnFbQr.addEventListener('click', () => {
          this.closeModal();
          this.dispatchIntent({
            intent: 'qr_payment',
            targetView: 'check',
            targetSubtab: 'subtab-qr'
          });
        });
      }

      const btnFbHelp = document.getElementById('voiceFallbackLostMoney');
      if (btnFbHelp) {
        btnFbHelp.addEventListener('click', () => {
          this.closeModal();
          this.dispatchIntent({
            intent: 'lost_money',
            targetView: 'help',
            targetSubtab: null
          });
        });
      }
    },

    bindPasteButton() {
      const btnPaste = document.getElementById('btnVoiceAutoPaste');
      const smsInput = document.getElementById('smsInput');

      if (btnPaste && smsInput) {
        btnPaste.addEventListener('click', async () => {
          let pastedText = '';
          try {
            if (navigator.clipboard && typeof navigator.clipboard.readText === 'function') {
              pastedText = await navigator.clipboard.readText();
            }
          } catch (clipErr) {
            console.warn('[VoiceHelper] Clipboard readText denied/failed:', clipErr);
          }

          if (pastedText && pastedText.trim()) {
            smsInput.value = pastedText.trim();
            if (window.App) window.App.showToast('✓ संदेश पेस्ट हो गया (Message pasted)');
            this.handlePostPasteAnalysis(smsInput.value);
          } else {
            // Inform user to long press
            const pastePromptText = document.getElementById('voicePastePromptText');
            if (pastePromptText) {
              pastePromptText.textContent = window.I18n ? window.I18n.t('voice_paste_longpress', '👉 बॉक्स को दबाकर रखें और पेस्ट करें (Long-press inside box & tap Paste)') : '👉 बॉक्स को दबाकर रखें और पेस्ट करें';
            }
            if (window.App) {
              window.App.showToast('बॉक्स पर दबाकर रखें और पेस्ट करें (Long press to paste)');
            }
            smsInput.focus();
          }
        });

        // Also watch for manual paste / input in the box
        smsInput.addEventListener('input', () => {
          const val = smsInput.value.trim();
          if (val.length > 15 && this.isPastePromptActive()) {
            this.handlePostPasteAnalysis(val);
          }
        });
      }
    },

    isPastePromptActive() {
      const banner = document.getElementById('voicePasteBanner');
      return banner && banner.style.display !== 'none';
    },

    async handlePostPasteAnalysis(text) {
      if (!text || text.length < 5) return;
      this.stopPromptAudio();
      if (window.MessageDetector) {
        await window.MessageDetector.analyzeMessage();
        setTimeout(() => {
          this.readVerdictAloud();
        }, 400);
      }
    },

    readVerdictAloud() {
      this.stopPromptAudio();
      const verdictBox = document.getElementById('smsVerdictBox');
      const lang = (window.I18n && window.I18n.currentLang) ? window.I18n.currentLang : 'hi';
      if (!verdictBox) return;

      if (verdictBox.classList.contains('danger')) {
        const inputVal = (document.getElementById('smsInput')?.value || '').toLowerCase();
        let cat = 'extortion';
        if (inputVal.includes('otp') || inputVal.includes('ओटीपी')) cat = 'otp';
        else if (inputVal.includes('pin') || inputVal.includes('upi') || inputVal.includes('पिन')) cat = 'upi_pin';
        else if (inputVal.includes('police') || inputVal.includes('cbi') || inputVal.includes('arrest') || inputVal.includes('पुलिस')) cat = 'police';
        else if (inputVal.includes('kyc') || inputVal.includes('pan') || inputVal.includes('bank') || inputVal.includes('खाता')) cat = 'bank_kyc';
        else if (inputVal.includes('apk') || inputVal.includes('app') || inputVal.includes('download')) cat = 'remote_access';

        this.playPromptAudio(`alert_${cat}_${lang}.wav`, 'खतरा! यह संदेश संदिग्ध साइबर ठगी हो सकता है। किसी से OTP या PIN शेयर न करें।');
      } else if (verdictBox.classList.contains('safe')) {
        this.playPromptAudio('alert_chime.wav', 'यह संदेश सुरक्षित प्रतीत होता है।');
      } else {
        this.playPromptAudio(`alert_bank_kyc_${lang}.wav`, 'सावधान! इस संदेश की पुष्टि अपने बैंक या संबंधित विभाग से करें।');
      }
    },

    openModal() {
      const modal = document.getElementById('voiceModalOverlay');
      if (modal) modal.classList.add('open');
      this.resetModalUi();
    },

    closeModal() {
      this.isFlowActive = false;
      if (window.VoiceEngine && window.VoiceEngine.isListening) {
        window.VoiceEngine.stop('user_closed');
      }
      this.stopPromptAudio();
      const modal = document.getElementById('voiceModalOverlay');
      if (modal) modal.classList.remove('open');
    },

    resetModalUi() {
      const pulseWrap = document.getElementById('voicePulseWrap');
      const statusTitle = document.getElementById('voiceStatusTitle');
      const transcriptBox = document.getElementById('voiceTranscriptLive');
      const fallbackGrid = document.getElementById('voiceFallbackGrid');
      const tryAgainBtn = document.getElementById('btnVoiceTryAgain');
      const progressWrap = document.getElementById('voiceProgressWrap');

      if (pulseWrap) pulseWrap.className = 'voice-pulse-wrap listening';
      if (statusTitle) {
        statusTitle.textContent = window.I18n ? window.I18n.t('voice_status_listening', 'सुन रहे हैं... (Listening…)') : 'सुन रहे हैं... (Listening…)';
      }
      if (transcriptBox) {
        transcriptBox.textContent = '...';
        transcriptBox.classList.remove('has-text');
      }
      if (fallbackGrid) fallbackGrid.style.display = 'none';
      if (tryAgainBtn) tryAgainBtn.style.display = 'none';
      if (progressWrap) progressWrap.style.display = 'none';
    },

    async startListeningFlow() {
      if (this.isFlowActive) {
        console.log('[VoiceHelper] Voice flow is already in progress');
        return;
      }
      this.isFlowActive = true;
      this.stopPromptAudio();
      this.openModal();

      const lang = (window.I18n && window.I18n.currentLang) ? window.I18n.currentLang : 'hi';
      const statusTitle = document.getElementById('voiceStatusTitle');
      const transcriptBox = document.getElementById('voiceTranscriptLive');
      const progressWrap = document.getElementById('voiceProgressWrap');
      const progressBar = document.getElementById('voiceProgressBar');
      const progressText = document.getElementById('voiceProgressText');

      // Play "listening" spoken audio prompt
      this.playPromptAudio(`voice_listening_${lang}.wav`, (lang === 'en' ? 'Listening. Please speak now.' : 'सुन रहे हैं। कृपया बोलिए।'));

      if (!window.VoiceEngine) {
        this.showFallbackOptions('Speech engine not available');
        return;
      }

      await window.VoiceEngine.start({
        lang: lang,
        onProgress: (pct, msg) => {
          if (progressWrap && progressBar && progressText) {
            progressWrap.style.display = 'block';
            progressBar.style.width = `${pct}%`;
            progressText.textContent = msg;
          }
        },
        onListening: () => {
          if (progressWrap) progressWrap.style.display = 'none';
          if (statusTitle) {
            statusTitle.textContent = window.I18n ? window.I18n.t('voice_status_listening', 'सुन रहे हैं... (Listening…)') : 'सुन रहे हैं... (Listening…)';
          }
        },
        onPartial: (partialText) => {
          this.stopPromptAudio();
          if (transcriptBox) {
            transcriptBox.textContent = `"${partialText}"`;
            transcriptBox.classList.add('has-text');
          }
        },
        onTranscript: (finalText) => {
          this.stopPromptAudio();
          this.isFlowActive = false;
          if (transcriptBox) {
            transcriptBox.textContent = `"${finalText}"`;
            transcriptBox.classList.add('has-text');
          }
          this.processRecognizedTranscript(finalText);
        },
        onError: (err) => {
          console.warn('[VoiceHelper] Speech recognition error:', err);
          this.isFlowActive = false;
          this.retryCount++;
          this.showFallbackOptions(err.message || 'Permission or hardware error');
        },
        onEnd: (endInfo) => {
          this.isFlowActive = false;
          if (!this.currentIntentResult && endInfo.reason === 'timeout') {
            this.retryCount++;
            if (this.retryCount >= 2) {
              this.showFallbackOptions('Timeout after 2 attempts');
            } else {
              if (statusTitle) {
                statusTitle.textContent = window.I18n ? window.I18n.t('voice_status_timeout', 'कोई आवाज़ सुनाई नहीं दी (No speech heard)') : 'कोई आवाज़ सुनाई नहीं दी';
              }
              const tryAgainBtn = document.getElementById('btnVoiceTryAgain');
              if (tryAgainBtn) tryAgainBtn.style.display = 'inline-block';
            }
          }
        }
      });
    },

    processRecognizedTranscript(transcript) {
      if (!transcript || !transcript.trim()) {
        this.retryCount++;
        if (this.retryCount >= 2) {
          this.showFallbackOptions('Empty speech after 2 tries');
        }
        return;
      }

      if (!window.VoiceMatcher) {
        this.showFallbackOptions('Voice matcher missing');
        return;
      }

      const match = window.VoiceMatcher.match(transcript);
      console.log('[VoiceHelper] Intent match result:', match);

      if (match && match.intent) {
        this.retryCount = 0;
        this.currentIntentResult = match;
        const statusTitle = document.getElementById('voiceStatusTitle');
        if (statusTitle) {
          statusTitle.textContent = window.I18n ? window.I18n.t('voice_status_understood', 'समझ गए! (Understood!)') : 'समझ गए! (Understood!)';
        }

        // Slight pause so the user sees the recognized text, then navigate
        setTimeout(() => {
          this.closeModal();
          this.dispatchIntent(match);
        }, 600);
      } else {
        this.retryCount++;
        if (this.retryCount >= 2) {
          this.showFallbackOptions('No intent matched after 2 tries');
        } else {
          const statusTitle = document.getElementById('voiceStatusTitle');
          if (statusTitle) {
            statusTitle.textContent = window.I18n ? window.I18n.t('voice_status_unrecognized', 'माफ़ कीजिए, समझ नहीं पाए। (Could not understand)') : 'माफ़ कीजिए, समझ नहीं पाए।';
          }
          const tryAgainBtn = document.getElementById('btnVoiceTryAgain');
          if (tryAgainBtn) tryAgainBtn.style.display = 'inline-block';
        }
      }
    },

    dispatchIntent(intentResult) {
      const lang = (window.I18n && window.I18n.currentLang) ? window.I18n.currentLang : 'hi';
      const { intent, subType, targetView, targetSubtab } = intentResult;

      // 1. Navigate to target view and subtab
      if (window.App) {
        window.App.navigate(targetView);
        if (targetSubtab) {
          window.App.switchSubtab(targetSubtab);
        }
      }

      // 2. Intent-Specific Action Flow
      if (intent === 'whatsapp_or_sms_message') {
        const isWhatsapp = (subType === 'whatsapp');
        this.showPasteWorkflowBanner(isWhatsapp, lang);

        const smsInput = document.getElementById('smsInput');
        if (smsInput) {
          smsInput.focus();
        }

        // Spoken prompt & text announcement
        const audioFile = isWhatsapp ? `voice_paste_whatsapp_${lang}.wav` : `voice_paste_sms_${lang}.wav`;
        const fallbackText = isWhatsapp 
          ? (lang === 'en' ? 'Please paste the WhatsApp message here.' : 'कृपया व्हाट्सएप संदेश यहाँ पेस्ट करें।')
          : (lang === 'en' ? 'Please paste the SMS here.' : 'कृपया एसएमएस संदेश यहाँ पेस्ट करें।');

        this.playPromptAudio(audioFile, fallbackText);
      } else if (intent === 'phone_call') {
        if (window.App) window.App.showToast('📞 कॉल जांच अनुभाग (Call Check Active)');
      } else if (intent === 'qr_payment') {
        if (window.App) window.App.showToast('📷 UPI क्यूआर जांचें (Scan or Check QR)');
      } else if (intent === 'lost_money') {
        if (window.App) {
          window.App.showToast('🚨 आपातकालीन 1930 सहायता (Call 1930 Helpline)');
          // Emphasize 1930 emergency card
          const helpCallCard = document.getElementById('helpCallCard');
          if (helpCallCard) {
            helpCallCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            helpCallCard.classList.add('pulse-highlight');
            setTimeout(() => helpCallCard.classList.remove('pulse-highlight'), 3000);
          }
        }
      } else if (intent === 'learn') {
        if (window.App) window.App.showToast('📚 सुरक्षा पाठ एवं क्विज (Safety Lessons)');
      }
    },

    showPasteWorkflowBanner(isWhatsapp, lang) {
      const banner = document.getElementById('voicePasteBanner');
      const textEl = document.getElementById('voicePastePromptText');
      const subEl = document.getElementById('voicePasteSubText');
      const iconEl = document.getElementById('voicePasteIcon');

      if (!banner) return;

      banner.style.display = 'flex';
      banner.classList.add('active');

      if (isWhatsapp) {
        if (iconEl) iconEl.textContent = '💬';
        if (textEl) {
          textEl.textContent = window.I18n 
            ? window.I18n.t('voice_prompt_paste_whatsapp', 'कृपया व्हाट्सएप संदेश यहाँ पेस्ट करें (Paste WhatsApp message here)') 
            : 'कृपया व्हाट्सएप संदेश यहाँ पेस्ट करें';
        }
        if (subEl) {
          subEl.textContent = window.I18n
            ? window.I18n.t('voice_prompt_paste_sub', 'नीचे "पेस्ट करें" बटन दबाएं या बॉक्स में दबाकर रखें')
            : 'नीचे "पेस्ट करें" बटन दबाएं या बॉक्स में दबाकर रखें';
        }
      } else {
        if (iconEl) iconEl.textContent = '✉️';
        if (textEl) {
          textEl.textContent = window.I18n 
            ? window.I18n.t('voice_prompt_paste_sms', 'कृपया एसएमएस संदेश यहाँ पेस्ट करें (Paste SMS here)') 
            : 'कृपया एसएमएस संदेश यहाँ पेस्ट करें';
        }
        if (subEl) {
          subEl.textContent = window.I18n
            ? window.I18n.t('voice_prompt_paste_sub', 'नीचे "पेस्ट करें" बटन दबाएं या बॉक्स में दबाकर रखें')
            : 'नीचे "पेस्ट करें" बटन दबाएं या बॉक्स में दबाकर रखें';
        }
      }

      banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    },

    showFallbackOptions(reason = '') {
      console.log('[VoiceHelper] Activating Fallback 4-Button Menu. Reason:', reason);
      const pulseWrap = document.getElementById('voicePulseWrap');
      const statusTitle = document.getElementById('voiceStatusTitle');
      const fallbackGrid = document.getElementById('voiceFallbackGrid');
      const tryAgainBtn = document.getElementById('btnVoiceTryAgain');

      if (pulseWrap) pulseWrap.className = 'voice-pulse-wrap fallback';
      if (fallbackGrid) fallbackGrid.style.display = 'grid';
      if (tryAgainBtn) tryAgainBtn.style.display = 'inline-block';

      const lang = (window.I18n && window.I18n.currentLang) ? window.I18n.currentLang : 'hi';
      const promptText = (lang === 'en')
        ? 'Sorry, please tap one of these options.'
        : (lang === 'chg' ? 'माफ करव, एमा ले एक ठो चुनव।' : 'माफ़ कीजिए, कृपया इनमें से एक विकल्प चुनें।');

      if (statusTitle) {
        statusTitle.textContent = promptText;
      }

      this.playPromptAudio(`voice_fallback_${lang}.wav`, promptText);
    },

    playPromptAudio(fileName, fallbackSpokenText = '') {
      this.stopPromptAudio();
      const currentToken = ++this.playbackToken;
      const audioPath = `assets/alerts/${fileName}`;

      const player = new Audio(audioPath);
      this.audioPlayer = player;

      player.play().catch((audioErr) => {
        // If playback was aborted, paused, or interrupted by newer prompt, IGNORE!
        if (audioErr && (audioErr.name === 'AbortError' || audioErr.code === 20)) {
          return;
        }
        // If this player is no longer the active playback request, do nothing!
        if (this.playbackToken !== currentToken) {
          return;
        }

        console.warn(`[VoiceHelper] Could not play ${audioPath}, falling back to Web Speech:`, audioErr);
        // Fallback 1: Local SpeechSynthesis (offline)
        if (fallbackSpokenText && window.speechSynthesis) {
          try {
            if (this.playbackToken !== currentToken) return;
            window.speechSynthesis.cancel();
            const lang = (window.I18n && window.I18n.currentLang) ? window.I18n.currentLang : 'hi';
            const utt = new SpeechSynthesisUtterance(fallbackSpokenText);
            utt.lang = (lang === 'en') ? 'en-IN' : 'hi-IN';
            utt.rate = 0.95;
            window.speechSynthesis.speak(utt);
          } catch (synthErr) {
            console.warn('[VoiceHelper] SpeechSynthesis fallback notice:', synthErr);
          }
        }
      });
    },

    stopPromptAudio() {
      this.playbackToken++;
      if (this.audioPlayer) {
        try {
          this.audioPlayer.onended = null;
          this.audioPlayer.onerror = null;
          this.audioPlayer.pause();
          this.audioPlayer.currentTime = 0;
          this.audioPlayer.src = '';
        } catch (e) {}
        this.audioPlayer = null;
      }
      if (window.speechSynthesis) {
        try {
          window.speechSynthesis.cancel();
        } catch (e) {}
      }
    }
  };

  global.VoiceHelper = VoiceHelper;
})(typeof window !== 'undefined' ? window : globalThis);
