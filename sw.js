// CB6 & Beyond — Service Worker
const CACHE_VERSION = 'cb6-v1409';
const CORE_ASSETS = [
  '/',
  '/index.html',
  '/cb6-parking-explorer.html',
  '/cb6-crime-explorer.html',
  '/cb6-sanitation-explorer.html',
  '/cb6-parking-map.html',
  '/welcome.html',
  '/privacy.html',
  '/cb6-logo.png',
  '/manifest.json',
  '/app-home/hero-button.png',
  '/app-home/btn-bk.png',
  '/app-home/btn-mn.png',
  '/app-home/btn-qn.png',
  '/app-home/btn-bx.png',
  '/app-home/btn-si.png',
  '/app-home/btn-nyc.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) =>
      Promise.all(
        CORE_ASSETS.map((url) => cache.add(url).catch(() => null))
      )
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names.filter((n) => n !== CACHE_VERSION).map((n) => caches.delete(n))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Always network-first for live override/data files (never serve stale)
  if (url.pathname === '/heat.json' || url.pathname.endsWith('/heat.json')) {
    event.respondWith(fetch(req).catch(() => caches.match(req)));
    return;
  }

  // Data files change without the page changing, so never serve them from cache first.
  // Fall back to the cached copy only when the network is unavailable.
  if (url.pathname.startsWith('/data/') ||
      url.pathname.endsWith('.json') || url.pathname.endsWith('.geojson')) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) { const copy = res.clone(); caches.open(CACHE_VERSION).then((c) => c.put(req, copy)); }
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // Network-first for HTML — fallback to cached version only, never index.html
  const accept = req.headers.get('accept') || '';
  if (req.destination === 'document' || accept.indexOf('text/html') !== -1) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // Network-first for images so updated icons refresh promptly
  if (req.destination === 'image') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) { const copy = res.clone(); caches.open(CACHE_VERSION).then((cache) => cache.put(req, copy)); }
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // Cache-first for static assets
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(req, copy));
        }
        return res;
      });
    })
  );
});
