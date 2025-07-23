// 唯一的 DOM 載入完成事件監聽器，作為整個應用的進入點
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  console.log(path);
  // 根據 URL 路徑，執行對應頁面的初始化函式
  if (path.includes('trail.html')) {
    loadTrailDetails();
  } else if (path.includes('plan.html')) {
    loadPlanPage();
  } else {
    // 預設載入首頁
    loadTrailCards();
  }
});


// ==========================================================
// --- 首頁邏輯 (index.html) ---
// ==========================================================
async function loadTrailCards() {
  try {
    // 假設您有一個後端 API 提供步道列表
    const response = await fetch('/api/trails');
    if (!response.ok) throw new Error('Network response was not ok');
    const trails = await response.json();
    const grid = document.getElementById('trail-grid');
    if (!grid) return;
    grid.innerHTML = trails.map(trail => `
            <a href="/trail.html?id=${trail.id}" class="trail-card">
                <div class="card-content">
                    <h3>${trail.name}</h3>
                    <p><i class="fa-solid fa-map-marker-alt"></i> ${trail.location}</p>
                    <p><strong>難易度:</strong> ${trail.difficulty}</p>
                </div>
            </a>
        `).join('');
  } catch (error) {
    console.error('無法載入步道列表:', error);
    const grid = document.getElementById('trail-grid');
    if (grid) grid.innerHTML = `<p>無法載入步道列表，請稍後再試。</p>`;
  }
}


// ==========================================================
// --- 步道詳情頁邏輯 (trail.html) ---
// ==========================================================
async function loadTrailDetails() {
  const urlParams = new URLSearchParams(window.location.search);
  const trailId = urlParams.get('id');
  if (!trailId) {
    window.location.href = '/';
    return;
  }

  try {
    // 1. 獲取步道基本資料
    // 假設您有一個後端 API `/api/trails/:id`
    const trailRes = await fetch(`/api/trails/${trailId}`);
    if (!trailRes.ok) throw new Error('Trail not found');
    const trail = await trailRes.json();

    // 2. 顯示步道資訊
    displayTrailInfo(trail);

    // 3. 獲取天氣資訊 (可選)
    const weatherResponse = await fetch(`/api/weather/${trail.weatherStation.locationName}`);
    if (!weatherResponse.ok) throw new Error('無法取得天氣資料');
    const weather = await weatherResponse.json();
    displayWeatherForecast(weather);

    // 4. *** 關鍵：為 GPX 分析按鈕設定點擊事件 ***
    //document.getElementById('gpx-analyze-btn').addEventListener('click', handleGpxUpload);

  } catch (error) {
    console.error('無法載入步道詳情:', error);
    document.getElementById('trail-name').textContent = '找不到步道資料';
  }
}

function displayTrailInfo(trail) {
  document.title = `${trail.name} - 步道詳情`;
  document.getElementById('trail-name').textContent = trail.name;
  document.getElementById('trail-location').textContent = trail.location;
  document.getElementById('planning-link').href = `/plan.html?id=${trail.id}`; // 確保連結正確

  const statsGrid = document.getElementById('stats-grid');
  statsGrid.innerHTML = `
        <div class="stat-item"><i class="fa-solid fa-clock"></i><div class="label">總時間</div><div class="value">${trail.stats.totalTime}</div></div>
        <div class="stat-item"><i class="fa-solid fa-route"></i><div class="label">總移動距離</div><div class="value">${trail.stats.distance}</div></div>
        <div class="stat-item"><i class="fa-solid fa-arrow-trend-up"></i><div class="label">總爬升高度</div><div class="value">${trail.stats.ascent}</div></div>
        <div class="stat-item"><i class="fa-solid fa-arrow-trend-down"></i><div class="label">總下降高度</div><div class="value">${trail.stats.descent}</div></div>
        <div class="stat-item"><i class="fa-solid fa-layer-group"></i><div class="label">難易度</div><div class="value">${trail.difficulty}</div></div>
        <div class="stat-item"><i class="fa-solid fa-id-card"></i><div class="label">申請入山</div><div class="value">${trail.permitRequired ? '是' : '否'}</div></div>
    `;
}

function displayWeatherForecast(weather) {
  try {
    const container = document.getElementById('weather-forecast');
    container.innerHTML = '';
    weather.forEach(entry => {
      const card = document.createElement('div');
      card.className = 'weather-card';
      card.innerHTML = `
            <h3>${entry.time}</h3>
            <p>🌡️ ${entry.temp}°C</p>
            <p>🌧️ 降雨機率：${entry.pop === '-' ? 'N/A' : entry.pop + '%'}</p>
            <p>🌤️ 天氣：${entry.wx}</p>
        `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error('天氣資料錯誤：', err);
    const container = document.getElementById('weather');
    container.innerHTML = '<p>無法載入天氣資訊。</p>';

  }
}

// ==========================================================
// --- 路線規劃頁邏輯 (plan.html) ---
// ==========================================================
// ✨ 更新後的路線規劃頁邏輯
async function loadPlanPage() {
  const urlParams = new URLSearchParams(window.location.search);
  const trailId = urlParams.get('id');

  // --- 設定 GPX 上傳按鈕的事件監聽 ---
  const analyzeBtn = document.getElementById('gpx-analyze-btn');
  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', handlePlanPageGpxUpload);
  }

  // === 初始化 map_plan 並從 IndexedDB 顯示圖磚 ===
  const mapPlanContainer = document.getElementById('map_plan');
  if (mapPlanContainer && !mapPlanContainer._leaflet_id) {
    const map_plan = L.map('map_plan').setView([24, 121], 13);

    // const offlineTileLayer = new L.TileLayer.IndexedDB(); // 已定義在你原本程式中
    // offlineTileLayer.addTo(map_plan);

    const offlineTileLayer = L.tileLayer.indexedDB(); // 已定義在你原本程式中
    offlineTileLayer.addTo(map_plan);

    // 加入使用者 GPX 的顯示功能（若有）
    const gpxInput = document.getElementById('gpx-file-input');
    if (gpxInput) {
      gpxInput.addEventListener('change', function (e) {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function (event) {
          const gpxText = event.target.result;
          const gpxLayer = new L.GPX(gpxText, {
            async: true,
            marker_options: {
              startIconUrl: 'libs/leaflet/images/icon_blue.png',
              shadowUrl: '/libs/leaflet/images/marker-shadow.png',
              endIconUrl: '/libs/leaflet/images/icon_red.png',
            }
          });

          gpxLayer.on('loaded', function (e) {
            map_plan.fitBounds(e.target.getBounds());
          });

          gpxLayer.addTo(map_plan);
        };
        reader.readAsText(file);
      });
    }
  }
}

// ✨ 全新的函式：處理規劃頁的 GPX 上傳
async function handlePlanPageGpxUpload() {
  const fileInput = document.getElementById('gpx-file-input');
  const timelineDisplay = document.getElementById('gpx-timeline-display');

  if (fileInput.files.length === 0) {
    timelineDisplay.innerHTML = '<p style="color: red;">請先選擇一個 GPX 檔案。</p>';
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('gpxFile', file);

  timelineDisplay.innerHTML = '<p>分析中，請稍候...</p>';

  try {
    const response = await fetch('/api/gpxanalyzer', {
      method: 'POST',
      body: formData,
    });
    const result = await response.json();

    if (!response.ok) { throw new Error(result.message || '分析失敗'); }

    displayGpxTimeline(result);

  } catch (error) {
    timelineDisplay.innerHTML = `<p style="color: red;">分析出錯: ${error.message}</p>`;
  }
}

// ✨ 全新的函式：將後端回傳的資料渲染成時間軸
function displayGpxTimeline(data) {
  const timelineDisplay = document.getElementById('gpx-timeline-display');

  if (!data.waypoints || data.waypoints.length === 0) {
    timelineDisplay.innerHTML = '<p>此 GPX 檔案中未找到可顯示的航點 (Waypoints)。</p>';
    return;
  }

  // 顯示總結資訊
  const summaryHtml = `
        <div class="timeline-summary">
            <span><i class="fa-solid fa-clock"></i> ${data.summary.totalTime}</span>
            <span><i class="fa-solid fa-route"></i> ${data.summary.distance}</span>
            <span><i class="fa-solid fa-arrow-trend-up"></i> ${data.summary.ascent}</span>
        </div>
    `;

  // 產生每個航點的 HTML
  const waypointsHtml = data.waypoints.map((point, index) => `
        <div class="timeline-item">
            <div class="timeline-marker">
                <div class="number">${index + 1}</div>
                ${point.time ? `<div class="time-bubble">${point.time}</div>` : ''}
            </div>
            <div class="timeline-content">
                <div class="name">${point.name || '未命名航點'}</div>
                <div class="elevation">${point.elevation}</div>
            </div>
            <div class="timeline-connector"></div>
        </div>
    `).join('');

  timelineDisplay.innerHTML = summaryHtml + waypointsHtml;
}

// ==========================================================
// --- 地圖載入 (trail.html) ---
// ==========================================================
const map_trail_container = document.getElementById('map_trail');
let map_trail;
if (map_trail_container && !map_trail_container._leaflet_id) {
  map_trail = L.map('map_trail').setView([24, 121], 8);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map_trail);

  const fileInput = document.getElementById('gpx-file-input');
  fileInput.addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (event) {
      const gpxText = event.target.result;

      // 將 gpx 文字餵給 leaflet-gpx（支援文字）
      const gpxLayer = new L.GPX(gpxText, {
        async: true,
        marker_options: {
          startIconUrl: 'libs/leaflet/images/icon_blue.png',
          shadowUrl: '/libs/leaflet/images/marker-shadow.png',
          endIconUrl: '/libs/leaflet/images/icon_red.png',
        }
      });

      gpxLayer.on('loaded', function (e) {
        map_trail.fitBounds(e.target.getBounds());
      });

      gpxLayer.addTo(map_trail);
    };

    reader.readAsText(file);
  });
}

// ====== IndexedDB 操作 ======
const DB_NAME = 'offline-map-db';
const TILE_STORE = 'tiles';
const STATIC_STORE = 'static';

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = function (e) {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(TILE_STORE)) db.createObjectStore(TILE_STORE);
      if (!db.objectStoreNames.contains(STATIC_STORE)) db.createObjectStore(STATIC_STORE);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function saveTileToDB(key, blob) {
  try {
    const db = await openDB();
    const tx = db.transaction(TILE_STORE, 'readwrite');
    tx.objectStore(TILE_STORE).put(blob, key);
    await tx.complete;
    // 新增 debug log
    console.log('已存入tile:', key);
  } catch (e) {
    console.error('存tile進IndexedDB失敗:', key, e);
  }
}

async function getTileFromDB(key) {
  const db = await openDB();
  return new Promise((resolve) => {
    const req = db.transaction(TILE_STORE).objectStore(TILE_STORE).get(key);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => resolve(null);
  });
}

async function saveStaticToDB(key, blob) {
  const db = await openDB();
  const tx = db.transaction(STATIC_STORE, 'readwrite');
  tx.objectStore(STATIC_STORE).put(blob, key);
  return tx.complete;
}

async function getStaticFromDB(key) {
  const db = await openDB();
  return new Promise((resolve) => {
    const req = db.transaction(STATIC_STORE).objectStore(STATIC_STORE).get(key);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => resolve(null);
  });
}

// ====== GPX 上傳後分析tile範圍 ======
async function handleGpxUpload(file) {
  // 取得進度條元素
  const progressDiv = document.getElementById('download-progress');
  const progressBar = document.getElementById('progress-bar');
  const progressText = document.getElementById('progress-text');
  if (progressDiv) {
    progressDiv.style.display = '';
    progressBar.value = 0;
    progressText.textContent = '開始下載圖磚...';
  }

  // 1. 解析GPX取得經緯度範圍
  const text = await file.text();
  const parser = new DOMParser();
  const xml = parser.parseFromString(text, "application/xml");
  const lats = Array.from(xml.querySelectorAll("trkpt")).map(pt => parseFloat(pt.getAttribute("lat")));
  const lons = Array.from(xml.querySelectorAll("trkpt")).map(pt => parseFloat(pt.getAttribute("lon")));
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLon = Math.min(...lons), maxLon = Math.max(...lons);

  // 2. 計算所需z/x/y範圍 (以15~16級為例)
  function lon2tile(lon, z) { return Math.floor((lon + 180) / 360 * Math.pow(2, z)); }
  function lat2tile(lat, z) {
    return Math.floor(
      (1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, z)
    );
  }
  const zooms = [15, 16];
  let tiles = [];
  zooms.forEach(z => {
    const x1 = lon2tile(minLon, z), x2 = lon2tile(maxLon, z);
    const y1 = lat2tile(maxLat, z), y2 = lat2tile(minLat, z);
    for (let x = x1; x <= x2; x++) {
      for (let y = y1; y <= y2; y++) {
        tiles.push({ z, x, y });
      }
    }
  });

  // 3. 呼叫API下載圖磚zip
  if (progressText) progressText.textContent = '下載圖磚壓縮包...';
  const resp = await fetch('/api/tiles/download', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tiles })
  });

  if (!resp.ok) {
    if (progressDiv) progressDiv.style.display = 'none';
    let msg = '下載圖磚時發生錯誤';
    try {
      const err = await resp.json();
      msg = err.message || msg;
    } catch (e) { }
    alert(msg);
    return;
  }

  const zipBlob = await resp.blob();

  // 嘗試用 JSZip 解壓，若不是 zip 會報錯
  let zip;
  try {
    zip = await JSZip.loadAsync(zipBlob);
  } catch (e) {
    if (progressDiv) progressDiv.style.display = 'none';
    alert('伺服器回傳的不是有效的圖磚壓縮包，請稍後再試。');
    return;
  }
  const fileNames = Object.keys(zip.files);
  if (fileNames.length === 0) {
    if (progressDiv) progressDiv.style.display = 'none';
    alert('圖磚壓縮包內沒有任何檔案，請檢查API回傳。');
    return;
  }
  let count = 0;
  const pngFiles = fileNames.filter(fn => fn.endsWith('.png'));
  const total = pngFiles.length;
  for (const [idx, filename] of pngFiles.entries()) {
    const blob = await zip.files[filename].async('blob');
    await saveTileToDB(filename, blob);
    count++;
    if (progressBar) progressBar.value = Math.round((count / total) * 100);
    if (progressText) progressText.textContent = `正在儲存圖磚 (${count}/${total})`;
  }
  if (progressBar) progressBar.value = 100;
  if (progressText) progressText.textContent = '完成！';
  setTimeout(() => {
    if (progressDiv) progressDiv.style.display = 'none';
  }, 1200);
  alert(`離線地圖圖磚已存入本機！共存入 ${count} 張圖磚。`);
}

// ====== Leaflet 自訂tileLayer從IndexedDB取tile ======
L.TileLayer.IndexedDB = L.TileLayer.extend({
  getTileUrl: function (coords) {
    return `${coords.z}/${coords.x}/${coords.y}.png`;
  },
  createTile: function (coords, done) {
    const key = this.getTileUrl(coords);
    const img = document.createElement('img');
    img.alt = '';
    img.setAttribute('role', 'presentation');
    getTileFromDB(key).then(blob => {
      if (blob) {
        img.src = URL.createObjectURL(blob);
      } else {
        // fallback: 線上取得
        img.src = `https://tile.openstreetmap.org/${key}`;
      }
      done(null, img);
    });
    return img;
  }
});

//Add
L.tileLayer.indexedDB = function (opts) {
  return new L.TileLayer.IndexedDB(undefined, opts);
};

// ====== 存靜態資源進IndexedDB (首次啟動時) ======
async function cacheStatics() {
  const statics = [
    '/index.html', '/plan.html', '/trail.html', '/script.js', '/styles.css',
    '/manifest.json', '/libs/leaflet/leaflet.css', '/libs/leaflet/leaflet.js',
    '/libs/leaflet/images/marker-icon.png', '/libs/leaflet/images/marker-icon-2x.png',
    '/libs/leaflet/images/marker-shadow.png'
  ];
  for (const url of statics) {
    const resp = await fetch(url);
    if (resp.ok) {
      const blob = await resp.blob();
      await saveStaticToDB(url, blob);
    }
  }
}

// ====== trail.html GPX上傳事件掛載 ======
document.addEventListener('DOMContentLoaded', () => {
  // ...existing code...
  const gpxInput = document.getElementById('gpx-file-input');
  const downloadMapBtn = document.getElementById('download-map-btn');
  let lastGpxFile = null;

  if (gpxInput) {
    gpxInput.addEventListener('change', (e) => {
      lastGpxFile = e.target.files[0];
    });
  }
  if (downloadMapBtn) {
    downloadMapBtn.addEventListener('click', async () => {
      if (!lastGpxFile) {
        alert('請先選擇一個 GPX 檔案');
        return;
      }
      await handleGpxUpload(lastGpxFile);
    });
  }
  // 首次啟動時存靜態資源
  cacheStatics();
  // ...existing code...
});

// Service Worker 與 IndexedDB 協作：監聽 SW 請求
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.addEventListener('message', async (event) => {
    const data = event.data;
    if (data && data.type === 'GET_IDB') {
      let result = null;
      if (data.dbType === 'tiles') {
        result = await getTileFromDB(data.key);
      } else if (data.dbType === 'static') {
        result = await getStaticFromDB(data.key);
      }
      if (result) {
        // 讀出 ArrayBuffer
        const arrayBuffer = await result.arrayBuffer();
        event.ports[0].postMessage({
          found: true,
          buffer: arrayBuffer,
          contentType: result.type
        }, [arrayBuffer]);
      } else {
        event.ports[0].postMessage({ found: false });
      }
    }
  });
}
