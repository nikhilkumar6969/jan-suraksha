// Jan Suraksha Service Worker - Production PWA Offline Engine
const CACHE_NAME = 'suraksha-v3.0';

// Function to handle HTTP Range requests (206 Partial Content) for offline video streaming
async function handleRangeRequest(request, cachedResponse) {
  const rangeHeader = request.headers.get('range');
  if (!rangeHeader) {
    return cachedResponse;
  }

  const arrayBuffer = await cachedResponse.arrayBuffer();
  const total = arrayBuffer.byteLength;
  const match = rangeHeader.match(/bytes=(\d*)-(\d*)/);

  if (!match) {
    return cachedResponse;
  }

  let start = match[1] ? parseInt(match[1], 10) : 0;
  let end = match[2] ? parseInt(match[2], 10) : total - 1;

  if (start >= total || end >= total || start > end) {
    return new Response(null, {
      status: 416,
      statusText: 'Range Not Satisfiable',
      headers: {
        'Content-Range': `bytes */${total}`
      }
    });
  }

  const slicedBuffer = arrayBuffer.slice(start, end + 1);
  const headers = new Headers(cachedResponse.headers);
  headers.set('Content-Range', `bytes ${start}-${end}/${total}`);
  headers.set('Content-Length', slicedBuffer.byteLength.toString());
  headers.set('Accept-Ranges', 'bytes');
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'video/mp4');
  }

  return new Response(slicedBuffer, {
    status: 206,
    statusText: 'Partial Content',
    headers: headers
  });
}

// Essential Shell & Core Application Assets (Mandatory for offline functionality)
const REQUIRED_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json',
  '/css/tokens.css',
  '/css/app.css',
  '/js/app.js',
  '/js/hero-slider.js',
  '/js/i18n.js',
  '/js/detector.js',
  '/js/offline_classifier.js',
  '/js/qr.js',
  '/js/trai_header_ui.js',
  '/js/call.js',
  '/js/pcm-recorder-processor.js',
  '/js/learn.js',
  '/js/help.js',
  '/js/reports.js',
  '/js/dashboard.js',
  '/js/crypto_verify.js',
  '/js/voice_matcher.js',
  '/js/voice_engine.js',
  '/js/voice_helper.js',
  '/locales/en.json',
  '/locales/hi.json',
  '/locales/chg.json',
  '/content/lessons_en.json',
  '/content/lessons_hi.json',
  '/content/lessons_chg.json',
  '/content/quiz_en.json',
  '/content/quiz_hi.json',
  '/content/quiz_chg.json',
  '/content/headers.json',
  '/content/voice_intents.json',
  '/content/scam_model_weights.json',
  '/assets/icons/favicon.png',
  '/assets/icons/icon-192.png',
  '/assets/icons/icon-512.png',
  '/assets/icons/logo.png',
  '/assets/bg.jpg',
  '/assets/banner.jpg'
];

// Optional / Large Media Assets (Cached individually with try/catch resilience)
const OPTIONAL_MEDIA_ASSETS = [
  '/js/vendor/vosk.js',
  '/assets/alerts/voice_listening_en.wav',
  '/assets/alerts/voice_listening_hi.wav',
  '/assets/alerts/voice_listening_chg.wav',
  '/assets/alerts/voice_paste_whatsapp_en.wav',
  '/assets/alerts/voice_paste_whatsapp_hi.wav',
  '/assets/alerts/voice_paste_whatsapp_chg.wav',
  '/assets/alerts/voice_paste_sms_en.wav',
  '/assets/alerts/voice_paste_sms_hi.wav',
  '/assets/alerts/voice_paste_sms_chg.wav',
  '/assets/alerts/voice_fallback_en.wav',
  '/assets/alerts/voice_fallback_hi.wav',
  '/assets/alerts/voice_fallback_chg.wav',
  '/assets/models/vosk-model-hi.tar.gz',
  '/assets/models/vosk-model-en.tar.gz',
  '/assets/videos/upi_safety.mp4',
  '/assets/videos/report_1930.mp4',
  '/assets/alerts/alert_chime.wav',
  '/assets/alerts/alert_bank_kyc_hi.wav',
  '/assets/alerts/alert_bank_kyc_en.wav',
  '/assets/alerts/alert_bank_kyc_chg.wav',
  '/assets/alerts/alert_otp_hi.wav',
  '/assets/alerts/alert_otp_en.wav',
  '/assets/alerts/alert_otp_chg.wav',
  '/assets/alerts/alert_police_hi.wav',
  '/assets/alerts/alert_police_en.wav',
  '/assets/alerts/alert_police_chg.wav',
  '/assets/alerts/alert_extortion_hi.wav',
  '/assets/alerts/alert_extortion_en.wav',
  '/assets/alerts/alert_extortion_chg.wav',
  '/assets/alerts/alert_remote_access_hi.wav',
  '/assets/alerts/alert_remote_access_en.wav',
  '/assets/alerts/alert_remote_access_chg.wav',
  '/assets/alerts/alert_upi_pin_hi.wav',
  '/assets/alerts/alert_upi_pin_en.wav',
  '/assets/alerts/alert_upi_pin_chg.wav',
  '/assets/samples/bank_kyc_call.wav',
  '/assets/samples/digital_arrest_call.wav',
  '/assets/samples/fedex_customs_call.wav',
  '/assets/backgrounds/media_1795408750990_34d08dd7.jpg',
  '/assets/backgrounds/media_1795408780895_a44d0d97.jpg',
  '/assets/backgrounds/media_1795408792868_3844933b.jpg',
  '/assets/backgrounds/media_1795408807123_f835ec6f.jpg',
  '/assets/backgrounds/media_1795408866473_e3ecd55a.jpg',
  '/assets/backgrounds/elderly_villagers_technology.jpg',
  '/assets/backgrounds/indian_farmers.jpg',
  '/assets/backgrounds/rural_chhattisgarh_village.jpg',
  '/assets/backgrounds/rural_community_cyber_safety.jpg',
  '/assets/backgrounds/rural_women_digital_awareness.jpg'
];

// Install Event: Cache required shell with addAll, then cache optional media with individual try/catch
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      console.log(`[ServiceWorker ${CACHE_NAME}] Pre-caching core required application shell...`);
      // 1. Mandatory Core Assets: Atomic addAll
      await cache.addAll(REQUIRED_ASSETS);
      console.log(`[ServiceWorker ${CACHE_NAME}] Required assets pre-cached.`);

      // 2. Optional Media Assets: Fault-tolerant individual fetches
      for (const assetUrl of OPTIONAL_MEDIA_ASSETS) {
        try {
          const res = await fetch(assetUrl);
          if (res && res.ok) {
            await cache.put(assetUrl, res);
          }
        } catch (err) {
          console.warn(`[ServiceWorker ${CACHE_NAME}] Optional asset skipped:`, assetUrl, err);
        }
      }
      console.log(`[ServiceWorker ${CACHE_NAME}] All assets processed.`);
    }).then(() => self.skipWaiting())
  );
});

// Activate Event: Purge older cache generations and claim clients immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log(`[ServiceWorker] Purging legacy cache: ${key}`);
            return caches.delete(key);
          }
        })
      );
    }).then(() => {
      console.log(`[ServiceWorker ${CACHE_NAME}] Claiming clients.`);
      return self.clients.claim();
    })
  );
});

// Fetch Event: Stratified Routing and Offline Handling
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // 1. Non-GET requests (e.g. POST /api/reports/submit) are network-only
  if (request.method !== 'GET') {
    return;
  }

  // 2. /api/ requests: Network-Only with clean offline JSON response
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request).catch(() => {
        return new Response(
          JSON.stringify({
            status: 'offline',
            error: 'Backend API unreachable. Operating in offline mode.',
            is_offline: true,
            offline: true
          }),
          {
            status: 503,
            statusText: 'Service Unavailable (Offline)',
            headers: { 'Content-Type': 'application/json' }
          }
        );
      })
    );
    return;
  }

  // 3. Navigation Requests: Network-First with fallback to cached /index.html
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.ok) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return networkResponse;
        })
        .catch(async () => {
          const cachedIndex = await caches.match('/index.html');
          if (cachedIndex) return cachedIndex;
          const fallback = await caches.match('/offline.html');
          if (fallback) return fallback;
          return new Response('Jan Suraksha Offline', {
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
          });
        })
    );
    return;
  }

  // 4. Static Assets (CSS, JS, Fonts, Images, Audio, Videos, JSON): Cache-First with Network Fallback & Range Support
  event.respondWith(
    (async () => {
      // Check cache first (ignoreSearch and normalize pathname)
      let cachedResponse = await caches.match(request, { ignoreSearch: true });
      if (!cachedResponse && url.pathname) {
        cachedResponse = await caches.match(url.pathname, { ignoreSearch: true });
      }

      if (cachedResponse) {
        if (request.headers.has('range')) {
          return handleRangeRequest(request, cachedResponse);
        }
        // Asynchronously update non-video static assets in background if online (Stale-While-Revalidate)
        if (!url.pathname.endsWith('.mp4')) {
          fetch(request)
            .then((networkResponse) => {
              if (networkResponse && networkResponse.status === 200) {
                caches.open(CACHE_NAME).then((cache) => cache.put(request, networkResponse));
              }
            })
            .catch(() => {});
        }
        return cachedResponse;
      }

      // Not in cache, fetch from network
      try {
        const networkResponse = await fetch(request);
        // Only cache full 200 OK responses (Cache API fails on 206 Partial Content)
        if (networkResponse && networkResponse.status === 200) {
          const copy = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        }
        return networkResponse;
      } catch (err) {
        // If an image fails to load offline, provide empty or fallback response
        if (request.destination === 'image') {
          const fallbackLogo = await caches.match('/assets/icons/logo.png');
          if (fallbackLogo) return fallbackLogo;
        }
        return new Response('', { status: 408, statusText: 'Request Offline' });
      }
    })()
  );
});
