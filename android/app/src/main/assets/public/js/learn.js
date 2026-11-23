// Suraksha Offline Lessons & Scenario Quiz Engine
const LearnManager = {
  lessons: [],
  quiz: [],
  currentLessonIdx: 0,
  currentQuizIdx: 0,
  quizScore: 0,
  userAnswers: [],

  async init() {
    await this.loadContent();

    const btnPrev = document.getElementById('btnPrevLesson');
    const btnNext = document.getElementById('btnNextLesson');
    const btnAudio = document.getElementById('btnLessonAudio');
    const btnNextQ = document.getElementById('btnNextQuiz');

    if (btnPrev) btnPrev.addEventListener('click', () => this.changeLesson(-1));
    if (btnNext) btnNext.addEventListener('click', () => this.changeLesson(1));
    if (btnAudio) btnAudio.addEventListener('click', () => this.readLesson());
    if (btnNextQ) btnNextQ.addEventListener('click', () => this.nextQuizQuestion());

    window.addEventListener('languageChanged', async () => {
      await this.loadContent();
      this.renderCurrentLesson();
      this.renderCurrentQuiz();
      this.updateHomeScoreRing();
    });

    this.renderCurrentLesson();
    this.renderCurrentQuiz();
    this.updateHomeScoreRing();
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

  changeLesson(delta) {
    if (!this.lessons.length) return;
    this.currentLessonIdx = (this.currentLessonIdx + delta + this.lessons.length) % this.lessons.length;
    this.renderCurrentLesson();
  },

  renderCurrentLesson() {
    if (!this.lessons.length) return;
    const item = this.lessons[this.currentLessonIdx];

    const lTopic = document.getElementById('lessonTopicName');
    const lTitle = document.getElementById('lessonTitle');
    const lSum = document.getElementById('lessonSummary');
    const lRule = document.getElementById('lessonRule');
    const lCounter = document.getElementById('lessonCounter');

    if (lTopic) lTopic.textContent = `${item.topic} (${this.currentLessonIdx + 1} / ${this.lessons.length})`;
    if (lTitle) lTitle.textContent = item.title;
    if (lSum) lSum.textContent = item.summary;
    if (lRule) lRule.textContent = item.rule;
    if (lCounter) lCounter.textContent = `${this.currentLessonIdx + 1} / ${this.lessons.length}`;
  },

  readLesson() {
    if (!this.lessons.length || !window.speechSynthesis) return;
    const item = this.lessons[this.currentLessonIdx];
    const textToRead = `${item.title}. ${item.summary} ${item.rule}`;
    const utterance = new SpeechSynthesisUtterance(textToRead);
    utterance.lang = (I18n.currentLang === 'en') ? 'en-IN' : 'hi-IN';
    utterance.rate = 0.9;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    if (window.App) window.App.showToast('पाठ सुनाया जा रहा है (Playing lesson)');
  },

  renderCurrentQuiz() {
    if (!this.quiz.length) return;
    const item = this.quiz[this.currentQuizIdx];

    const pNum = document.getElementById('quizProgressNum');
    const qText = document.getElementById('quizQuestionText');
    const optList = document.getElementById('quizOptionsList');
    const fbBox = document.getElementById('quizFeedbackBox');
    const btnNext = document.getElementById('btnNextQuiz');
    const scoreTracker = document.getElementById('quizScoreTracker');

    if (pNum) pNum.textContent = `QUESTION ${this.currentQuizIdx + 1} OF ${this.quiz.length} (${item.topic})`;
    if (qText) qText.textContent = item.question;
    if (fbBox) fbBox.style.display = 'none';
    if (btnNext) btnNext.style.display = 'none';
    if (scoreTracker) scoreTracker.textContent = `Score: ${this.quizScore}`;

    if (optList) {
      optList.innerHTML = '';
      item.options.forEach((optText, idx) => {
        const btn = document.createElement('button');
        btn.className = 'quiz-opt-btn';
        btn.innerHTML = `<span style="width:24px; height:24px; border-radius:50%; background:var(--border-color); display:inline-flex; align-items:center; justify-content:center; font-size:12px; font-weight:700;">${String.fromCharCode(65 + idx)}</span> <span>${optText}</span>`;
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
    if (scoreTracker) scoreTracker.textContent = `Score: ${this.quizScore}`;

    const fbBox = document.getElementById('quizFeedbackBox');
    if (fbBox) {
      fbBox.style.display = 'block';
      fbBox.style.backgroundColor = isCorrect ? 'var(--status-safe-bg)' : 'var(--status-danger-bg)';
      fbBox.style.border = `1.5px solid ${isCorrect ? 'var(--status-safe)' : 'var(--status-danger)'}`;
      fbBox.style.color = isCorrect ? 'var(--status-safe)' : 'var(--status-danger)';
      fbBox.innerHTML = `<strong>${isCorrect ? '✓ सही उत्तर (Correct!)' : '✗ गलत उत्तर (Incorrect!)'}</strong><div style="color:var(--text-main); margin-top:4px; font-size:14px;">${item.explanation}</div>`;
    }

    const btnNext = document.getElementById('btnNextQuiz');
    if (btnNext) {
      btnNext.style.display = 'inline-flex';
      btnNext.textContent = (this.currentQuizIdx === this.quiz.length - 1) ? 'स्कोर देखें (View Results) 🏆' : 'अगला सवाल (Next Question) ▶';
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

  renderQuizResults() {
    const container = document.getElementById('quizContainer');
    if (!container) return;

    const total = this.quizScore;
    let badgeText = I18n.t('score_badge_beginner', 'Beginner');
    let badgeKey = 'score_badge_beginner';
    if (total >= 90) {
      badgeText = I18n.t('score_badge_champion', 'Suraksha Champion');
      badgeKey = 'score_badge_champion';
    } else if (total >= 70) {
      badgeText = I18n.t('score_badge_safe', 'Safe Citizen');
      badgeKey = 'score_badge_safe';
    } else if (total >= 40) {
      badgeText = I18n.t('score_badge_aware', 'Aware');
      badgeKey = 'score_badge_aware';
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
      return `<div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:13px;">
        <span><strong>${t}</strong>: ${topicMap[t].correct}/${topicMap[t].total} correct</span>
        <span style="font-weight:700; color:${pct>=70 ? 'var(--status-safe)' : 'var(--status-danger)'};">${pct}%</span>
      </div>`;
    }).join('');

    container.innerHTML = `
      <div style="text-align: center; padding: 10px;">
        <div style="font-size: 3rem;">🏆</div>
        <h3 style="font-size: 1.6rem; font-weight: 800; color: var(--primary);">क्विज परिणाम (Quiz Completed)</h3>
        <div style="font-size: 2.2rem; font-weight: 800; color: var(--accent-warm); margin: 6px 0;">${total} / 100</div>
        <div class="score-badge" style="font-size: 14px; padding: 4px 12px; margin-bottom: 16px;">
          ${badgeText}
        </div>

        <div style="background: var(--bg-card-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 14px; text-align: left; margin: 16px 0;">
          <h4 style="font-size: 14px; margin-bottom: 10px; font-weight: 700;">विषयवार प्रदर्शन (Topic Breakdown):</h4>
          ${breakdownHtml}
        </div>

        <p style="font-size: 14px; color: var(--text-muted); margin-bottom: 16px;">
          सुझाव: कमजोर विषयों के लिए ऊपर दिए गए सुरक्षा कार्ड्स को दोबारा पढ़ें।
        </p>

        <button class="btn btn-primary" onclick="LearnManager.restartQuiz()">
          🔄 क्विज दोबारा खेलें (Restart Quiz)
        </button>
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
