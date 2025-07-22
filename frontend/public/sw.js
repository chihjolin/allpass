const CACHE_NAME = "gpx-pwa-cache-v1";
const urlsToCache = [
  "/index.html",
  "/plan.html",
  "/trail.html",
  "/script.js",
  "/styles.css",
  "/manifest.json",
  '/libs/leaflet/leaflet.css',
  '/libs/leaflet/leaflet.js',
  '/libs/leaflet/images/marker-icon.png',
  '/libs/leaflet/images/marker-icon-2x.png',
  '/libs/leaflet/images/marker-shadow.png',
//   "/桃山瀑布.gpx"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
