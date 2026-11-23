// Jan Suraksha Service Worker - Production PWA Offline Engine
const CACHE_NAME = 'suraksha-pwa-v3.0';

// Essential Shell & Offline Application Assets
const PRECACHE_ASSETS = [
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
  '/js/qr.js',
  '/js/whisper_stt.js',
  '/js/trai_header_ui.js',
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
  '/content/headers.json',
  '/assets/icons/favicon.png',
  '/assets/icons/icon-192.png',
  '/assets/icons/icon-512.png',
  '/assets/icons/logo.png',
  '/assets/bg.jpg',
  '/assets/banner.jpg',
  '/assets/alerts/alert_chime.wav'
];

// Install Event: Robust pre-caching with individual error resilience
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      console.log('[ServiceWorker] Pre-caching core application shell...');
      // Use map + Promise.allSettled so an optional missing asset doesn't abort worker installation
      const promises = PRECACHE_ASSETS.map((url) =>
        fetch(url)
          .then((response) => {
            if (response.ok) {
              return cache.put(url, response);
            }
            console.warn('[ServiceWorker] Pre-cache skipped non-ok asset:', url, response.status);
            return Promise.resolve();
          })
          .catch((err) => {
            console.warn('[ServiceWorker] Pre-cache fetch error for asset:', url, err);
            return Promise.resolve();
          })
      );
      await Promise.all(promises);
      console.log('[ServiceWorker] Core assets pre-cached successfully.');
    }).then(() => self.skipWaiting())
  );
});

// Activate Event: Clean up stale caches and claim clients immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[ServiceWorker] Purging legacy cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => {
      console.log('[ServiceWorker] Active & Claimed Clients.');
      return self.clients.claim();
    })
  );
});

// Fetch Event: Stratified Caching Logic
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // 1. Disallow non-GET requests from caching
  if (request.method !== 'GET') {
    // For POST/PUT requests (like report submissions or audio analysis)
    // Network first, return honest 503 if unreachable so client queues or falls back locally
    return;
  }

  // 2. API Endpoints: Network-First with honest status code fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          return networkResponse;
        })
        .catch(() => {
          // Return honest 503 Service Unavailable so client code knows backend is offline
          return new Response(
            JSON.stringify({
              status: 'offline',
              error: 'Backend API unreachable. Operating in offline mode.',
              is_offline: true
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

  // 3. Navigation Requests: Network-First with Cache fallback to index.html or offline.html
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          if (networkResponse.ok) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return networkResponse;
        })
        .catch(async () => {
          const cachedIndex = await caches.match('/index.html');
          if (cachedIndex) return cachedIndex;
          const cachedOffline = await caches.match('/offline.html');
          if (cachedOffline) return cachedOffline;
          return new Response('Jan Suraksha Offline. Please connect to the internet to load.', {
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
          });
        })
    );
    return;
  }

  // 4. Static Shell Assets (HTML/CSS/JS/Icons/Locales/Content): Cache-First with Network Stale-While-Revalidate
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        // Fetch in background to update cache for next load (stale-while-revalidate)
        fetch(request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
              caches.open(CACHE_NAME).then((cache) => cache.put(request, networkResponse));
            }
          })
          .catch(() => {});
        return cachedResponse;
      }

      // If not in cache, fetch from network and store in cache
      return fetch(request)
        .then((networkResponse) => {
          if (!networkResponse || networkResponse.status !== 200 || (networkResponse.type !== 'basic' && networkResponse.type !== 'cors')) {
            return networkResponse;
          }
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
          return networkResponse;
        })
        .catch(async () => {
          // If image fails, could return placeholder or empty response
          if (request.destination === 'image') {
            const fallbackIcon = await caches.match('/assets/icons/icon-192.png');
            if (fallbackIcon) return fallbackIcon;
          }
          return new Response('Resource unavailable offline', { status: 404 });
        });
    })
  );
});
