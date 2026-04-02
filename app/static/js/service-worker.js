// Simple service worker with caching

const CACHE_NAME = "flask-pwa-v1";
const urlsToCache = [
  "/",
  "/static/css/style.css",
];

// Install event: cache files
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
  );
});

// Fetch event: serve from cache if available
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});