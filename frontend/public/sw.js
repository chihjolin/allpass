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
  '/libs/leaflet/gpx.min.js',
  '/libs/leaflet/images/marker-icon.png',
  '/libs/leaflet/images/marker-icon-2x.png',
  '/libs/leaflet/images/marker-shadow.png',
  '/libs/leaflet/images/icon_blue.png',
  '/libs/leaflet/images/icon_red.png',
  '/libs/leaflet/images/icon_yellow.png',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  // "/桃山瀑布.gpx"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

// 讓 SW 能向 client 請求 IndexedDB 內容
async function getFromClient(event, dbType, key) {
  const allClients = await self.clients.matchAll({ type: 'window' });
  if (!allClients.length) return null;
  const client = allClients[0];
  return new Promise((resolve) => {
    const msgChannel = new MessageChannel();
    msgChannel.port1.onmessage = (e) => {
      if (e.data && e.data.found) {
        const arrayBuffer = e.data.buffer;
        const resp = new Response(arrayBuffer, { headers: { 'Content-Type': e.data.contentType || 'image/png' } });
        resolve(resp);
      } else {
        resolve(null);
      }
    };
    client.postMessage({ type: 'GET_IDB', dbType, key }, [msgChannel.port2]);
    setTimeout(() => resolve(null), 1500); // 最多等1.5秒
  });
}

// fetch事件: 先查cache, 若無則交給前端協助從IndexedDB取(僅註解說明, 需前端配合)
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  // 判斷是否為tile或靜態資源
  if (url.pathname.match(/^\/\d+\/\d+\/\d+\.png$/)) {
    // 地圖tile
    event.respondWith(
      caches.match(event.request).then(async (response) => {
        if (response) return response;
        // 試著從 IndexedDB 取
        const idbResp = await getFromClient(event, 'tiles', url.pathname.replace(/^\//, ''));
        if (idbResp) return idbResp;
        // fallback 線上
        return fetch(event.request);
      })
    );
  } else if (url.pathname.match(/\.(js|css|png|jpg|json|ico)$/)) {
    // 靜態資源
    event.respondWith(
      caches.match(event.request).then(async (response) => {
        if (response) return response;
        const idbResp = await getFromClient(event, 'static', url.pathname);
        if (idbResp) return idbResp;
        return fetch(event.request);
      })
    );
  } else if (
    url.pathname === "/trail.html" ||
    url.pathname === "/plan.html" ||
    url.pathname === "/index.html"
  ) {
    // 忽略 query string，統一回傳快取的主檔案
    event.respondWith(
      caches.match(url.pathname).then((response) => {
        return response || fetch(url.pathname);
      })
    );
  } else {
    // 其他請求照舊
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
  }
});
