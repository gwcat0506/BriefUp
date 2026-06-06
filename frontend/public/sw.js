// Service Worker — BrefUp PWA
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.clients.claim());

self.addEventListener('fetch', (event) => {
  // 네트워크 우선 전략
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
