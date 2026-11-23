// Suraksha Service Worker - Offline Caching Strategy
const CACHE_NAME = 'suraksha-v2.2';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/css/tokens.css',
  '/css/app.css',
  '/js/app.js',
  '/js/hero-slider.js',
  '/js/i18n.js',
  '/js/detector.js',
  '/js/qr.js',
  '/js/call.js',
  '/js/pcm-recorder-processor.js',
  '/js/learn.js',
  '/js/help.js',
  '/js/reports.js',
  '/js/dashboard.js',
  '/js/crypto_verify.js',
  '/locales/en.json',
  '/locales/hi.json',
  '/locales/chg.json',
  '/content/lessons_en.json',
  '/content/lessons_hi.json',
  '/content/lessons_chg.json',
  '/content/quiz_en.json',
  '/content/quiz_hi.json',
  '/content/quiz_chg.json',
  '/manifest.json',
  '/assets/bg.jpg',
  '/assets/banner.jpg',
  '/assets/backgrounds/media_1795408750990_34d08dd7.jpg',
  '/assets/backgrounds/media_1795408780895_a44d0d97.jpg',
  '/assets/backgrounds/media_1795408792868_3844933b.jpg',
  '/assets/backgrounds/media_1795408807123_f835ec6f.jpg',
  '/assets/backgrounds/media_1795408866473_e3ecd55a.jpg',
  '/assets/backgrounds/rural_chhattisgarh_village.jpg',
  '/assets/backgrounds/indian_farmers.jpg',
  '/assets/backgrounds/rural_women_digital_awareness.jpg',
  '/assets/backgrounds/rural_community_cyber_safety.jpg',
  '/assets/backgrounds/elderly_villagers_technology.jpg',
  '/assets/alerts/alert_chime.wav',
  '/assets/alerts/alert_upi_pin_hi.wav',
  '/assets/alerts/alert_upi_pin_chg.wav',
  '/assets/alerts/alert_upi_pin_en.wav',
  '/assets/alerts/alert_otp_hi.wav',
  '/assets/alerts/alert_otp_chg.wav',
  '/assets/alerts/alert_otp_en.wav',
  '/assets/alerts/alert_police_hi.wav',
  '/assets/alerts/alert_police_chg.wav',
  '/assets/alerts/alert_police_en.wav',
  '/assets/alerts/alert_remote_access_hi.wav',
  '/assets/alerts/alert_remote_access_chg.wav',
  '/assets/alerts/alert_remote_access_en.wav',
  '/assets/alerts/alert_extortion_hi.wav',
  '/assets/alerts/alert_extortion_chg.wav',
  '/assets/alerts/alert_extortion_en.wav',
  '/assets/alerts/alert_bank_kyc_hi.wav',
  '/assets/alerts/alert_bank_kyc_chg.wav',
  '/assets/alerts/alert_bank_kyc_en.wav',
  '/assets/lessons/lesson_otp_hi.wav',
  '/assets/lessons/lesson_otp_chg.wav',
  '/assets/lessons/lesson_otp_en.wav',
  '/assets/lessons/lesson_atm_pin_hi.wav',
  '/assets/lessons/lesson_atm_pin_chg.wav',
  '/assets/lessons/lesson_atm_pin_en.wav',
  '/assets/lessons/lesson_upi_pin_hi.wav',
  '/assets/lessons/lesson_upi_pin_chg.wav',
  '/assets/lessons/lesson_upi_pin_en.wav',
  '/assets/lessons/lesson_qr_code_hi.wav',
  '/assets/lessons/lesson_qr_code_chg.wav',
  '/assets/lessons/lesson_qr_code_en.wav',
  '/assets/lessons/lesson_fake_bank_call_hi.wav',
  '/assets/lessons/lesson_fake_bank_call_chg.wav',
  '/assets/lessons/lesson_fake_bank_call_en.wav'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[ServiceWorker] Pre-caching offline assets');
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[ServiceWorker] Removing old cache', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // Offline-first for static assets, network-first with cache fallback for dynamic API endpoints
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({ 
          status: 'offline', 
          message: 'Offline mode active. Using local engine and queued actions.' 
        }), {
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
  } else {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(event.request).then((networkResponse) => {
          return caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        });
      }).catch(() => caches.match('/index.html'))
    );
  }
});
