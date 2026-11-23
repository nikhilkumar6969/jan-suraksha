// ============================================================================
// Jan Suraksha — Cinematic Hero Background Slider
// Automatically transitions rural Chhattisgarh photography behind hero section.
// Features: 5.5s interval, 1.8s crossfade, preloading, offline-first, reduced-motion.
// ============================================================================

const HeroSlider = {
  currentIndex: 0,
  intervalId: null,
  slides: [],
  intervalDuration: 5500, // 5.5 seconds per slide (5–6s requirement)
  isPaused: false,

  slideData: [
    {
      id: 0,
      title: 'Rural Chhattisgarh Village',
      url: '/assets/backgrounds/media_1795408750990_34d08dd7.jpg',
      fallback: '/assets/backgrounds/rural_chhattisgarh_village.jpg'
    },
    {
      id: 1,
      title: 'Indian Farmers',
      url: '/assets/backgrounds/media_1795408780895_a44d0d97.jpg',
      fallback: '/assets/backgrounds/indian_farmers.jpg'
    },
    {
      id: 2,
      title: 'Rural Women and Digital Awareness',
      url: '/assets/backgrounds/media_1795408792868_3844933b.jpg',
      fallback: '/assets/backgrounds/rural_women_digital_awareness.jpg'
    },
    {
      id: 3,
      title: 'Rural Community and Cyber Safety',
      url: '/assets/backgrounds/media_1795408807123_f835ec6f.jpg',
      fallback: '/assets/backgrounds/rural_community_cyber_safety.jpg'
    },
    {
      id: 4,
      title: 'Elderly Villagers and Technology',
      url: '/assets/backgrounds/media_1795408866473_e3ecd55a.jpg',
      fallback: '/assets/backgrounds/elderly_villagers_technology.jpg'
    }
  ],

  init() {
    const sliderContainer = document.getElementById('heroSlider');
    if (!sliderContainer) return;

    // Ensure all 5 slides are present in the DOM
    let slideElements = sliderContainer.querySelectorAll('.hero-slide');
    if (slideElements.length < this.slideData.length) {
      sliderContainer.innerHTML = '';
      this.slideData.forEach((item, idx) => {
        const slide = document.createElement('div');
        slide.className = 'hero-slide' + (idx === 0 ? ' active' : '');
        slide.style.backgroundImage = `url('${item.url}')`;
        slide.setAttribute('data-index', idx);
        slide.setAttribute('title', item.title);
        sliderContainer.appendChild(slide);
      });
      slideElements = sliderContainer.querySelectorAll('.hero-slide');
    }

    this.slides = Array.from(slideElements);
    if (this.slides.length === 0) return;

    // 1. Preload all background images to eliminate flicker during transitions
    this.preloadImages();

    // 2. Set active slide state on init
    this.currentIndex = 0;
    this.updateSlideDisplay();

    // 3. Start auto-rotation loop
    this.startAutoPlay();

    // 4. Pause when tab/window is hidden to preserve device resources, resume on focus
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.stopAutoPlay();
      } else {
        this.startAutoPlay();
      }
    });

    // 6. Listen for reduced motion preference changes dynamically
    const motionMediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (motionMediaQuery.addEventListener) {
      motionMediaQuery.addEventListener('change', (e) => {
        if (e.matches) {
          this.pause();
        } else {
          this.startAutoPlay();
        }
      });
    }
  },

  preloadImages() {
    this.slideData.forEach((item, idx) => {
      const img = new Image();
      img.src = item.url;
      img.onload = () => {
        // Image successfully preloaded
      };
      img.onerror = () => {
        console.warn(`[HeroSlider] Failed to load ${item.url}, attempting fallback: ${item.fallback}`);
        if (this.slides[idx]) {
          this.slides[idx].style.backgroundImage = `url('${item.fallback}')`;
        }
      };
    });
  },

  updateSlideDisplay() {
    this.slides.forEach((slide, idx) => {
      if (idx === this.currentIndex) {
        slide.classList.add('active');
      } else {
        slide.classList.remove('active');
      }
    });
  },

  next() {
    if (this.slides.length === 0) return;
    this.currentIndex = (this.currentIndex + 1) % this.slides.length;
    this.updateSlideDisplay();
  },

  prev() {
    if (this.slides.length === 0) return;
    this.currentIndex = (this.currentIndex - 1 + this.slides.length) % this.slides.length;
    this.updateSlideDisplay();
  },

  goTo(index) {
    if (index >= 0 && index < this.slides.length) {
      this.currentIndex = index;
      this.updateSlideDisplay();
    }
  },

  startAutoPlay() {
    this.stopAutoPlay();
    this.intervalId = setInterval(() => {
      this.next();
    }, this.intervalDuration);
  },

  stopAutoPlay() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  },

  pause() {
    this.isPaused = true;
    this.stopAutoPlay();
  },

  resume() {
    this.isPaused = false;
    this.startAutoPlay();
  }
};

window.HeroSlider = HeroSlider;
