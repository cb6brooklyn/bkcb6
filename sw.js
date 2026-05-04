const CACHE = "cb6-v7";
const OFFLINE = [
  "/bkcb6/og-image.png",
  "/bkcb6/manifest.json"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(OFFLINE)));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  const isHtmlNavigation = e.request.mode === 'navigate' || url.pathname.endsWith('.html');
  // Never cache HTML — always fetch fresh, including cache-busted URLs
  if (isHtmlNavigation) {
    e.respondWith(
      fetch(e.request, { cache: 'reload' }).catch(() => caches.match(e.request))
    );
    return;
  }
  // Network-first for everything else
  e.respondWith(
    fetch(e.request)
      .then(r => {
        const clone = r.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
        return r;
      })
      .catch(() => caches.match(e.request))
  );
});