// Jan Suraksha - Offline Lessons, Video Storyboard & Scenario Quiz Engine
const LearnManager = {
  lessons: [],
  quiz: [],
  currentLessonIdx: 0,
  currentSceneIdx: 0,
  currentQuizIdx: 0,
  quizScore: 0,
  userAnswers: [],
  isVideoPlaying: false,
  videoTimer: null,
  currentAudioObj: null,
  isAudioPlaying: false,

  async init() {
    await this.loadContent();

    // Lesson Carousel & Navigation
    const btnPrev = document.getElementById('btnPrevLesson');
    const btnNext = document.getElementById('btnNextLesson');
    if (btnPrev) btnPrev.addEventListener('click', () => this.changeLesson(-1));
    if (btnNext) btnNext.addEventListener('click', () => this.changeLesson(1));

    // Topic Quick-Select Pills
    this.bindTopicPills();

    // Video Storyboard Controls
    const btnPlayVideo = document.getElementById('btnPlayVideo');
    const btnRestartVideo = document.getElementById('btnRestartVideo');
    const btnPrevScene = document.getElementById('btnPrevScene');
    const btnNextScene = document.getElementById('btnNextScene');

    if (btnPlayVideo) btnPlayVideo.addEventListener('click', () => this.toggleVideoPlay());
    if (btnRestartVideo) btnRestartVideo.addEventListener('click', () => this.restartVideo());
    if (btnPrevScene) btnPrevScene.addEventListener('click', () => this.changeScene(-1));
    if (btnNextScene) btnNextScene.addEventListener('click', () => this.changeScene(1));

    // Offline Audio Narration Button
    const btnAudio = document.getElementById('btnLessonAudio');
    if (btnAudio) btnAudio.addEventListener('click', () => this.toggleAudio());

    // Scroll to Quiz Button
    const btnScrollQuiz = document.getElementById('btnScrollToQuiz');
    if (btnScrollQuiz) {
      btnScrollQuiz.addEventListener('click', () => {
        const quizEl = document.getElementById('quizContainer');
        if (quizEl) quizEl.scrollIntoView({ behavior: 'smooth' });
      });
    }

    // Quiz Navigation
    const btnNextQ = document.getElementById('btnNextQuiz');
    if (btnNextQ) btnNextQ.addEventListener('click', () => this.nextQuizQuestion());

    // Language Change Listener
    window.addEventListener('languageChanged', async () => {
      this.stopAudio();
      this.stopVideo();
      await this.loadContent();
      this.renderCurrentLesson();
      this.renderCurrentQuiz();
      this.updateHomeScoreRing();
    });

    this.renderCurrentLesson();
    this.renderCurrentQuiz();
    this.updateHomeScoreRing();
    this.bindVideoCards();
  },

  bindVideoCards() {
    const cards = document.querySelectorAll('.video-card');
    const modal = document.getElementById('videoModalOverlay');
    const closeBtn = document.getElementById('btnVideoModalClose');
    const container = document.getElementById('videoPlayerContainer');
    const modalTitle = document.getElementById('videoModalTitleText');
    const extLink = document.getElementById('videoExternalLink');
    const btnToggleLocal = document.getElementById('btnToggleLocalVideo');
    const sourceCitation = document.getElementById('videoSourceCitation');

    const closeModal = () => {
      if (modal) modal.classList.remove('open');
      if (container) container.innerHTML = '';
      if (btnToggleLocal) btnToggleLocal.style.display = 'none';
    };

    if (closeBtn) closeBtn.onclick = closeModal;
    if (modal) {
      modal.onclick = (e) => {
        if (e.target === modal) closeModal();
      };
    }
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal && modal.classList.contains('open')) {
        closeModal();
      }
    });

    cards.forEach((card) => {
      const playBtn = card.querySelector('.video-watch-btn');
      const thumb = card.querySelector('.video-thumb-container');
      const titleEl = card.querySelector('.video-card-title');
      const videoId = card.getAttribute('data-video-id');
      const localSrc = card.getAttribute('data-local-src');
      const sourceTag = card.querySelector('.video-source-tag')?.textContent || 'CyberDost / I4C / RBI';

      const openVideo = () => {
        const title = titleEl ? titleEl.textContent.trim() : 'Cyber Safety Video';
        if (modalTitle) modalTitle.textContent = title;
        if (sourceCitation) sourceCitation.textContent = `Source: ${sourceTag}`;
        if (extLink) extLink.href = `https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}`;

        let isUsingLocal = false;

        const renderYouTube = () => {
          isUsingLocal = false;
          container.innerHTML = `
            <iframe 
              class="video-player-iframe" 
              src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?autoplay=1&rel=0&modestbranding=1" 
              title="${title.replace(/"/g, '&quot;')}" 
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
              allowfullscreen>
            </iframe>
          `;
          if (localSrc && btnToggleLocal) {
            btnToggleLocal.style.display = 'inline-block';
            btnToggleLocal.textContent = '📁 ऑफलाइन वीडियो चलाएं (Play Offline MP4)';
          }
        };

        const renderLocal = () => {
          isUsingLocal = true;
          container.innerHTML = `
            <video class="video-player-element" controls autoplay controlslist="nodownload">
              <source src="${encodeURI(localSrc)}" type="video/mp4">
              Your browser does not support HTML5 video.
            </video>
          `;
          if (btnToggleLocal) {
            btnToggleLocal.style.display = 'inline-block';
            btnToggleLocal.textContent = '🌐 यूट्यूब पर देखें (Play YouTube)';
          }
        };

        if (btnToggleLocal) {
          btnToggleLocal.onclick = (e) => {
            e.preventDefault();
            if (isUsingLocal) {
              renderYouTube();
            } else {
              renderLocal();
            }
          };
        }

        renderYouTube();
        if (modal) modal.classList.add('open');
      };

      if (thumb) thumb.onclick = openVideo;
      if (playBtn) playBtn.onclick = openVideo;
    });
  },

  async loadContent() {
    const lang = I18n.currentLang || 'hi';
    try {
      const resL = await fetch(`/content/lessons_${lang}.json`);
      if (resL.ok) this.lessons = await resL.json();

      const resQ = await fetch(`/content/quiz_${lang}.json`);
      if (resQ.ok) this.quiz = await resQ.json();
    } catch (e) {
      console.warn('Could not fetch lesson/quiz JSON offline:', e);
    }
  },

  bindTopicPills() {
    const pills = document.querySelectorAll('.lesson-topic-pill');
    pills.forEach((pill) => {
      pill.addEventListener('click', () => {
        const idx = parseInt(pill.getAttribute('data-topic-idx'), 10);
        if (!isNaN(idx) && idx >= 0 && idx < this.lessons.length) {
          this.currentLessonIdx = idx;
          this.currentSceneIdx = 0;
          this.stopAudio();
          this.stopVideo();
          this.renderCurrentLesson();
        }
      });
    });
  },

  changeLesson(delta) {
    if (!this.lessons.length) return;
    this.stopAudio();
    this.stopVideo();
    this.currentLessonIdx = (this.currentLessonIdx + delta + this.lessons.length) % this.lessons.length;
    this.currentSceneIdx = 0;
    this.renderCurrentLesson();
  },

  renderCurrentLesson() {
    if (!this.lessons.length) return;
    const item = this.lessons[this.currentLessonIdx];

    // Update Topic Pills Active State
    const pills = document.querySelectorAll('.lesson-topic-pill');
    pills.forEach((p, idx) => {
      p.classList.toggle('active', idx === this.currentLessonIdx);
    });

    // Header & Meta Elements
    const lTopic = document.getElementById('lessonTopicName');
    const lTitle = document.getElementById('lessonTitle');
    const lSum = document.getElementById('lessonSummary');
    const lRule = document.getElementById('lessonRule');
    const lCounter = document.getElementById('lessonCounter');
    const lBadge = document.getElementById('lessonBadge');

    if (lTopic) lTopic.textContent = `${item.topic} (${this.currentLessonIdx + 1} / ${this.lessons.length})`;
    if (lTitle) lTitle.textContent = item.title;
    if (lSum) lSum.textContent = item.summary;
    if (lRule) lRule.textContent = item.rule;
    if (lCounter) lCounter.textContent = `${this.currentLessonIdx + 1} / ${this.lessons.length}`;
    if (lBadge) lBadge.textContent = item.badge || '100% सुरक्षित';

    // Do's & Don'ts
    const doText = document.getElementById('lessonDoText');
    const dontText = document.getElementById('lessonDontText');
    if (doText) doText.textContent = item.do || 'हमेशा सतर्क और सावधान रहें।';
    if (dontText) dontText.textContent = item.dont || 'कभी किसी अनजान को गोपनीय जानकारी न दें।';

    // Render Video Storyboard Scene
    this.renderVideoScene();

    // Reset Audio Button
    this.updateAudioButtonState(false);
  },

  renderVideoScene() {
    if (!this.lessons.length) return;
    const item = this.lessons[this.currentLessonIdx];
    const steps = item.video_steps || [];
    if (!steps.length) return;

    if (this.currentSceneIdx >= steps.length) {
      this.currentSceneIdx = 0;
    }

    const currentStep = steps[this.currentSceneIdx];

    // Video Screen Elements
    const counterEl = document.getElementById('videoSceneCounter');
    const progressEl = document.getElementById('videoProgressBar');
    const emojiEl = document.getElementById('sceneVisualEmoji');
    const titleEl = document.getElementById('sceneTitle');
    const descEl = document.getElementById('sceneDesc');
    const sceneDisplay = document.getElementById('lessonSceneDisplay');

    if (counterEl) {
      counterEl.textContent = `दृश्य ${this.currentSceneIdx + 1} / ${steps.length} (Scene ${this.currentSceneIdx + 1} of ${steps.length})`;
    }
    if (progressEl) {
      progressEl.style.width = `${((this.currentSceneIdx + 1) / steps.length) * 100}%`;
    }

    if (sceneDisplay) {
      sceneDisplay.style.opacity = '0';
      setTimeout(() => {
        if (emojiEl) emojiEl.textContent = currentStep.visual || '🛡️';
        if (titleEl) titleEl.textContent = currentStep.title;
        if (descEl) descEl.textContent = currentStep.desc;
        sceneDisplay.style.transition = 'opacity 0.25s ease';
        sceneDisplay.style.opacity = '1';
      }, 100);
    } else {
      if (emojiEl) emojiEl.textContent = currentStep.visual || '🛡️';
      if (titleEl) titleEl.textContent = currentStep.title;
      if (descEl) descEl.textContent = currentStep.desc;
    }
  },

  toggleVideoPlay() {
    if (this.isVideoPlaying) {
      this.stopVideo();
    } else {
      this.startVideo();
    }
  },

  startVideo() {
    this.isVideoPlaying = true;
    const playIcon = document.getElementById('playIcon');
    const playText = document.getElementById('playText');
    const btnPlay = document.getElementById('btnPlayVideo');

    if (playIcon) playIcon.textContent = '⏸️';
    if (playText) playText.textContent = 'रोकें (Pause)';
    if (btnPlay) btnPlay.classList.add('active');

    // Also start narration audio if not already playing
    if (!this.isAudioPlaying) {
      this.playAudioFile();
    }

    if (this.videoTimer) clearInterval(this.videoTimer);
    this.videoTimer = setInterval(() => {
      const item = this.lessons[this.currentLessonIdx];
      const steps = item.video_steps || [];
      if (this.currentSceneIdx < steps.length - 1) {
        this.currentSceneIdx++;
        this.renderVideoScene();
      } else {
        // Reached end of scenes
        this.stopVideo();
      }
    }, 4000);
  },

  stopVideo() {
    this.isVideoPlaying = false;
    if (this.videoTimer) {
      clearInterval(this.videoTimer);
      this.videoTimer = null;
    }
    const playIcon = document.getElementById('playIcon');
    const playText = document.getElementById('playText');
    const btnPlay = document.getElementById('btnPlayVideo');

    if (playIcon) playIcon.textContent = '▶️';
    if (playText) playText.textContent = 'चलाएं (Play)';
    if (btnPlay) btnPlay.classList.remove('active');
  },

  restartVideo() {
    this.currentSceneIdx = 0;
    this.renderVideoScene();
    this.startVideo();
  },

  changeScene(delta) {
    if (!this.lessons.length) return;
    const item = this.lessons[this.currentLessonIdx];
    const steps = item.video_steps || [];
    if (!steps.length) return;

    this.currentSceneIdx = (this.currentSceneIdx + delta + steps.length) % steps.length;
    this.renderVideoScene();
  },

  toggleAudio() {
    if (this.isAudioPlaying) {
      this.stopAudio();
    } else {
      this.playAudioFile();
    }
  },

  playAudioFile() {
    if (!this.lessons.length) return;
    const item = this.lessons[this.currentLessonIdx];
    this.stopAudio();

    if (item.audio_file) {
      try {
        this.currentAudioObj = new Audio(item.audio_file);
        this.currentAudioObj.onplay = () => {
          this.isAudioPlaying = true;
          this.updateAudioButtonState(true);
        };
        this.currentAudioObj.onended = () => {
          this.stopAudio();
        };
        this.currentAudioObj.onerror = () => {
          console.warn('Audio file failed, falling back to speech synthesis');
          this.readLessonSynthesis();
        };
        this.currentAudioObj.play().catch(e => {
          console.warn('Autoplay prevented or audio load error:', e);
          this.readLessonSynthesis();
        });
        return;
      } catch (err) {
        console.warn('Audio element error:', err);
      }
    }
    this.readLessonSynthesis();
  },

  stopAudio() {
    if (this.currentAudioObj) {
      try {
        this.currentAudioObj.pause();
        this.currentAudioObj.currentTime = 0;
      } catch (e) {}
      this.currentAudioObj = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    this.isAudioPlaying = false;
    this.updateAudioButtonState(false);
  },

  updateAudioButtonState(isPlaying) {
    const audioBtnText = document.getElementById('audioBtnText');
    const audioWave = document.getElementById('audioWaveAnim');
    const btnAudio = document.getElementById('btnLessonAudio');

    if (audioBtnText) {
      audioBtnText.textContent = isPlaying 
        ? '⏸️ आवाज रोकें (Pause Audio)' 
        : '🔊 आवाज में सुनें (Offline Audio)';
    }
    if (audioWave) {
      audioWave.style.display = isPlaying ? 'inline-flex' : 'none';
    }
    if (btnAudio) {
      if (isPlaying) {
        btnAudio.classList.remove('btn-secondary');
        btnAudio.classList.add('btn-primary');
      }
    }
  },

  readLessonSynthesis() {
    if (!this.lessons.length || !window.speechSynthesis) return;
    const item = this.lessons[this.currentLessonIdx];
    const textToRead = `${item.title}. ${item.summary}. ${item.rule}`;
    const utterance = new SpeechSynthesisUtterance(textToRead);
    utterance.lang = (I18n.currentLang === 'en') ? 'en-IN' : 'hi-IN';
    utterance.rate = 0.9;

    utterance.onstart = () => {
      this.isAudioPlaying = true;
      this.updateAudioButtonState(true);
    };
    utterance.onend = () => {
      this.stopAudio();
    };
    utterance.onerror = () => {
      this.stopAudio();
    };

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    if (window.App) window.App.showToast('पाठ सुनाया जा रहा है (Playing offline voice)');
  },

  // -------------------------------------------------------------
  // Scenario Quiz Implementation
  // -------------------------------------------------------------
  renderCurrentQuiz() {
    if (!this.quiz.length) return;
    const item = this.quiz[this.currentQuizIdx];

    const pNum = document.getElementById('quizProgressNum');
    const qText = document.getElementById('quizQuestionText');
    const optList = document.getElementById('quizOptionsList');
    const fbBox = document.getElementById('quizFeedbackBox');
    const btnNext = document.getElementById('btnNextQuiz');
    const scoreTracker = document.getElementById('quizScoreTracker');

    if (pNum) pNum.textContent = `सवाल ${this.currentQuizIdx + 1} / ${this.quiz.length} (${item.topic})`;
    if (qText) qText.textContent = item.question;
    if (fbBox) fbBox.style.display = 'none';
    if (btnNext) btnNext.style.display = 'none';
    if (scoreTracker) scoreTracker.textContent = `Score: ${this.quizScore} / 100`;

    if (optList) {
      optList.innerHTML = '';
      item.options.forEach((optText, idx) => {
        const btn = document.createElement('button');
        btn.className = 'quiz-opt-btn';
        btn.innerHTML = `<span style="width:26px; height:26px; border-radius:50%; background:var(--border-strong); display:inline-flex; align-items:center; justify-content:center; font-size:13px; font-weight:800; color:var(--text-primary); flex-shrink:0;">${String.fromCharCode(65 + idx)}</span> <span style="line-height:1.4;">${optText}</span>`;
        btn.addEventListener('click', () => this.handleAnswerSelect(idx, btn));
        optList.appendChild(btn);
      });
    }
  },

  handleAnswerSelect(selectedIdx, clickedBtn) {
    const item = this.quiz[this.currentQuizIdx];
    const optButtons = document.querySelectorAll('.quiz-opt-btn');
    optButtons.forEach(b => b.disabled = true);

    const isCorrect = (selectedIdx === item.correct);
    if (isCorrect) {
      clickedBtn.classList.add('correct');
      this.quizScore += 10;
    } else {
      clickedBtn.classList.add('wrong');
      if (optButtons[item.correct]) {
        optButtons[item.correct].classList.add('correct');
      }
    }

    this.userAnswers.push({
      topic: item.topic,
      isCorrect,
      explanation: item.explanation
    });

    const scoreTracker = document.getElementById('quizScoreTracker');
    if (scoreTracker) scoreTracker.textContent = `Score: ${this.quizScore} / 100`;

    const fbBox = document.getElementById('quizFeedbackBox');
    if (fbBox) {
      fbBox.style.display = 'block';
      fbBox.style.backgroundColor = isCorrect ? 'var(--status-safe-bg)' : 'var(--status-danger-bg)';
      fbBox.style.border = `1.5px solid ${isCorrect ? 'var(--status-safe)' : 'var(--status-danger)'}`;
      fbBox.style.color = isCorrect ? 'var(--status-safe)' : 'var(--status-danger)';
      fbBox.innerHTML = `<strong>${isCorrect ? '✓ सही उत्तर (Correct!)' : '✗ गलत उत्तर (Incorrect!)'}</strong><div style="color:var(--text-main); margin-top:6px; font-size:14px; line-height:1.5;">${item.explanation}</div>`;
    }

    const btnNext = document.getElementById('btnNextQuiz');
    if (btnNext) {
      btnNext.style.display = 'inline-flex';
      btnNext.textContent = (this.currentQuizIdx === this.quiz.length - 1) ? 'स्कोर व प्रमाण पत्र देखें (View Results) 🏆' : 'अगला सवाल (Next Question) ▶';
    }
  },

  nextQuizQuestion() {
    if (this.currentQuizIdx < this.quiz.length - 1) {
      this.currentQuizIdx++;
      this.renderCurrentQuiz();
    } else {
      this.renderQuizResults();
    }
  },

  // -------------------------------------------------------------
  // Digital Financial Literacy Score & Certificate Generation
  // -------------------------------------------------------------
  renderQuizResults() {
    const container = document.getElementById('quizContainer');
    if (!container) return;

    const total = this.quizScore;
    let badgeText = I18n.t('score_badge_beginner', 'Beginner');
    let badgeKey = 'score_badge_beginner';
    let badgeEmoji = '📚';
    let badgeColor = 'var(--text-muted)';

    if (total >= 90) {
      badgeText = I18n.t('score_badge_champion', 'सुरक्षा चैंपियन (Suraksha Champion)');
      badgeKey = 'score_badge_champion';
      badgeEmoji = '🏆';
      badgeColor = '#0f766e';
    } else if (total >= 70) {
      badgeText = I18n.t('score_badge_safe', 'सुरक्षित नागरिक (Safe Citizen)');
      badgeKey = 'score_badge_safe';
      badgeEmoji = '🛡️';
      badgeColor = 'var(--status-safe)';
    } else if (total >= 40) {
      badgeText = I18n.t('score_badge_aware', 'जागरूक नागरिक (Aware Citizen)');
      badgeKey = 'score_badge_aware';
      badgeEmoji = '⚠️';
      badgeColor = 'var(--status-warn)';
    }

    // Persist to localStorage
    localStorage.setItem('suraksha_literacy_score', total);
    localStorage.setItem('suraksha_score_badge', badgeKey);

    // Topic breakdown
    const topicMap = {};
    this.userAnswers.forEach(a => {
      if (!topicMap[a.topic]) topicMap[a.topic] = { total: 0, correct: 0 };
      topicMap[a.topic].total++;
      if (a.isCorrect) topicMap[a.topic].correct++;
    });

    const breakdownHtml = Object.keys(topicMap).map(t => {
      const pct = Math.round((topicMap[t].correct / topicMap[t].total) * 100);
      const stars = (pct === 100) ? '⭐⭐⭐' : (pct >= 50) ? '⭐⭐' : '⭐';
      return `<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; font-size:13px; padding-bottom:4px; border-bottom:1px solid var(--border-subtle);">
        <span><strong>${t}</strong>: ${stars} (${topicMap[t].correct}/${topicMap[t].total})</span>
        <span style="font-weight:700; color:${pct>=70 ? 'var(--status-safe)' : 'var(--status-danger)'};">${pct}%</span>
      </div>`;
    }).join('');

    const todayDate = new Date().toLocaleDateString('hi-IN', { year: 'numeric', month: 'long', day: 'numeric' });

    container.innerHTML = `
      <div style="text-align: center; padding: 10px;">
        <div style="font-size: 3.5rem; margin-bottom: 8px;">${badgeEmoji}</div>
        <h3 style="font-size: 1.6rem; font-weight: 800; color: var(--primary);">डिजिटल वित्तीय साक्षरता स्कोर</h3>
        <p style="font-size: 14px; color: var(--text-muted); margin-bottom: 12px;">Digital Financial Literacy Score</p>
        
        <div style="font-size: 2.8rem; font-weight: 800; color: var(--accent-warm); margin: 6px 0;">${total} <span style="font-size:1.5rem; color:var(--text-muted);">/ 100</span></div>
        
        <div class="score-badge" style="font-size: 15px; padding: 6px 16px; margin-bottom: 16px; display:inline-block; background:${badgeColor}; color:#fff; border-radius:9999px;">
          ${badgeText}
        </div>

        <!-- Official Citizen Certificate -->
        <div class="literacy-certificate" id="literacyCertificate">
          <div class="certificate-seal">🏛️</div>
          <div class="certificate-title">डिजिटल वित्तीय साक्षरता प्रमाण पत्र</div>
          <div style="font-size: 12px; color: var(--text-muted); letter-spacing: 1px;">CERTIFICATE OF DIGITAL FINANCIAL LITERACY</div>
          <p style="font-size: 14px; margin-top: 14px;">प्रमाणित किया जाता है कि आपने जन सुरक्षा साइबर जागरूकता अभियान के अंतर्गत सभी 5 मुख्य सुरक्षा पाठ व क्विज पूर्ण किए हैं।</p>
          <div class="certificate-recipient">सत्यापित सुरक्षित नागरिक (Certified Safe Citizen)</div>
          <div style="display: flex; justify-content: space-around; margin-top: 16px; font-size: 13px; font-weight: 700;">
            <div>स्कोर: <span style="color:var(--accent);">${total} / 100</span></div>
            <div>श्रेणी: <span style="color:${badgeColor};">${badgeText}</span></div>
            <div>दिनांक: ${todayDate}</div>
          </div>
          <div style="margin-top: 14px; font-size: 11px; color: var(--text-muted);">
            जन सुरक्षा — छत्तीसगढ़ साइबर सुरक्षा व वित्तीय साक्षरता मिशन (Offline-first Verification)
          </div>
        </div>

        <!-- Topic Breakdown Section -->
        <div style="background: var(--bg-card-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 14px; text-align: left; margin: 16px 0;">
          <h4 style="font-size: 14px; margin-bottom: 12px; font-weight: 800; color: var(--primary);">विषयवार दक्षता रिपोर्ट (Topic Mastery Breakdown):</h4>
          ${breakdownHtml}
        </div>

        <div class="btn-row" style="justify-content: center; gap: 10px; margin-top: 16px; flex-wrap: wrap;">
          <button class="btn btn-secondary" onclick="window.print()">
            🖨️ प्रमाण पत्र प्रिंट / सेव करें (Print Certificate)
          </button>
          <button class="btn btn-primary" onclick="LearnManager.restartQuiz()">
            🔄 क्विज दोबारा खेलें (Restart Quiz)
          </button>
          <button class="btn btn-secondary" onclick="LearnManager.reviewLessons()">
            📚 पाठ दोबारा देखें (Review Lessons)
          </button>
        </div>
      </div>
    `;

    this.updateHomeScoreRing();
  },

  restartQuiz() {
    this.currentQuizIdx = 0;
    this.quizScore = 0;
    this.userAnswers = [];
    location.reload();
  },

  reviewLessons() {
    const cardEl = document.getElementById('lessonCardBox');
    if (cardEl) {
      cardEl.scrollIntoView({ behavior: 'smooth' });
    }
  },

  updateHomeScoreRing() {
    const savedScore = localStorage.getItem('suraksha_literacy_score') || 70;
    const scoreNum = parseInt(savedScore, 10);
    const badgeKey = localStorage.getItem('suraksha_score_badge') || 'score_badge_safe';

    const numEl = document.getElementById('homeScoreNumber');
    const badgeEl = document.getElementById('homeScoreBadge');
    const barEl = document.getElementById('scoreBarCircle');

    if (numEl) numEl.textContent = scoreNum;
    if (badgeEl) badgeEl.textContent = I18n.t(badgeKey, 'Safe Citizen');

    if (barEl) {
      // Circumference = 2 * PI * 40 = 251.2
      const offset = 251.2 - (251.2 * scoreNum) / 100;
      barEl.style.strokeDashoffset = offset;
    }
  }
};

window.LearnManager = LearnManager;
