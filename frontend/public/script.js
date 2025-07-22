// 唯一的 DOM 載入完成事件監聽器，作為整個應用的進入點
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
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
    // const weatherResponse = await fetch(`/api/weather/${trail.weatherStation.locationName}`);
    // const weather = await weatherResponse.json();
    // displayWeatherForecast(weather);

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

// *** 使用客戶端解析 GPX，不再依賴後端 API ***
// function handleGpxUpload() {
//     const fileInput = document.getElementById('gpx-file-input');
//     const resultArea = document.getElementById('gpx-result');

//     if (fileInput.files.length === 0) {
//         resultArea.innerHTML = '<p style="color: red;">請先選擇一個 GPX 檔案。</p>';
//         return;
//     }

//     const file = fileInput.files[0];
//     const reader = new FileReader();

//     reader.onload = (e) => {
//         try {
//             const gpxContent = e.target.result;
//             const gpx = new gpxParser(); // 使用 gpx-parser-js
//             gpx.parse(gpxContent);

//             if (!gpx.tracks || gpx.tracks.length === 0) {
//                 throw new Error("此 GPX 檔案不包含軌跡 (track) 資料。");
//             }

//             const track = gpx.tracks[0];
//             const distanceKm = (track.distance.total / 1000).toFixed(2);
//             const ascentM = Math.round(track.elevation.pos);
//             const descentM = Math.round(Math.abs(track.elevation.neg));

//             const startTime = new Date(track.points[0].time);
//             const endTime = new Date(track.points[track.points.length - 1].time);
//             const durationMs = endTime - startTime;
//             const hours = Math.floor(durationMs / 3600000);
//             const minutes = Math.round((durationMs % 3600000) / 60000);
//             const totalTime = `${hours} 小時 ${minutes} 分鐘`;

//             // 將結果顯示在畫面上
//             resultArea.innerHTML = `
//                 <h4>您的軌跡分析結果：</h4>
//                 <div class="stats-grid">
//                     <div class="stat-item"><div class="label">總時間</div><div class="value">${totalTime}</div></div>
//                     <div class="stat-item"><div class="label">總距離</div><div class="value">${distanceKm} km</div></div>
//                     <div class="stat-item"><div class="label">總爬升</div><div class="value">${ascentM} m</div></div>
//                     <div class="stat-item"><div class="label">總下降</div><div class="value">${descentM} m</div></div>
//                 </div>
//             `;
//         } catch (error) {
//             console.error("GPX 分析出錯:", error);
//             resultArea.innerHTML = `<p style="color: red;">分析出錯: ${error.message}</p>`;
//         }
//     };

//     reader.onerror = () => {
//         resultArea.innerHTML = `<p style="color: red;">讀取檔案失敗。</p>`;
//     };

//     resultArea.innerHTML = '<p>分析中，請稍候...</p>';
//     reader.readAsText(file);
// }

// ==========================================================
// --- 路線規劃頁邏輯 (plan.html) ---
// ==========================================================
async function loadPlanPage() {
  //     // === 1. 元素選擇 ===
  const gpxFileInput = document.getElementById('gpx-file-input');
  //     const trailNameEl = document.getElementById('plan-trail-name');
  //     const calculateBtn = document.getElementById('calculate-time-btn');
  //     const gpxFileNameSpan = document.getElementById('gpx-file-name');
  //     const timelineContainer = document.getElementById('gpx-timeline-container');
  //     const gpxSummary = document.getElementById('gpx-summary');

  // // === 2. 初始資料載入 (可選，如果需要的話) ===
  // // 如果 plan.html 需要顯示步道名稱，則保留這段
  // const urlParams = new URLSearchParams(window.location.search);
  // const trailId = urlParams.get('id');
  // if (trailId) {
  //     try {
  //         const trailRes = await fetch(`/api/trails/${trailId}`);
  //         if (!trailRes.ok) throw new Error('Trail not found for planning');
  //         const trail = await trailRes.json();
  //         trailNameEl.textContent = `規劃: ${trail.name}`;

  //         // 為時間計算機設定事件
  //         if (calculateBtn) {
  //             calculateBtn.addEventListener('click', () => calculateEstimatedTime(trail));
  //         }
  //     } catch (error) {
  //         trailNameEl.textContent = '無法載入步道資訊';
  //         console.error('無法載入步道 для規劃頁面:', error);
  //     }
  // } else {
  //     trailNameEl.textContent = '路線規劃'; // 提供一個通用標題
  // }

  // === 3. GPX 上傳與時間軸功能設定 ===
  if (gpxFileInput) {
    gpxFileInput.addEventListener('change', (event) => {
      const file = event.target.files[0];
      if (!file) return;
      gpxFileNameSpan.textContent = file.name;
      const reader = new FileReader();
      reader.onload = (e) => processGpxForTimeline(e.target.result, timelineContainer, gpxSummary);
      reader.readAsText(file);
    });
  }

  // === 初始化 map_plan 並從 IndexedDB 顯示圖磚 ===
  const mapPlanContainer = document.getElementById('map_plan');
  if (mapPlanContainer && !mapPlanContainer._leaflet_id) {
    const map_plan = L.map('map_plan').setView([24, 121], 13);

    const offlineTileLayer = new L.TileLayer.IndexedDB(); // 已定義在你原本程式中
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


// 地圖載入 (trail.html)
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

// === 全域或可重用的輔助函式 (Helper Functions) ===

// plan.html 專用的時間預估計算機
// function calculateEstimatedTime(trail) {
//   const speed = parseFloat(document.getElementById('pace-speed').value);
//   const ascentRate = parseFloat(document.getElementById('pace-ascent').value);
//   const distanceKm = parseFloat(trail.stats.distance);
//   const ascentM = parseFloat(trail.stats.ascent);
//   if (isNaN(speed) || isNaN(ascentRate)) {
//     alert('請輸入有效的數字');
//     return;
//   }
//   const timeForDistance = distanceKm / speed;
//   const timeForAscent = ascentM / ascentRate;
//   const totalHours = timeForDistance + timeForAscent;
//   const hours = Math.floor(totalHours);
//   const minutes = Math.round((totalHours - hours) * 60);
//   const resultDiv = document.getElementById('plan-result');
//   resultDiv.innerHTML = `預估您的健行時間約為：<br><strong>${hours} 小時 ${minutes} 分鐘</strong>`;
// }

// // plan.html 專用的 GPX 解析與時間軸渲染
// function processGpxForTimeline(gpxData, timelineContainer, gpxSummary) {
//   try {
//     const gpx = new gpxParser();
//     gpx.parse(gpxData);
//     let pointsForTimeline = [];
//     if (gpx.waypoints && gpx.waypoints.length > 0) {
//       pointsForTimeline = gpx.waypoints;
//     } else if (gpx.tracks && gpx.tracks.length > 0 && gpx.tracks[0].points.length > 0) {
//       pointsForTimeline = sampleTrackPoints(gpx.tracks[0].points, 5);
//     } else {
//       throw new Error("GPX 檔案不包含航點 (waypoints) 或軌跡 (tracks)。");
//     }
//     timelineContainer.innerHTML = '';
//     gpxSummary.style.display = 'flex';
//     renderSummary(gpx, pointsForTimeline);
//     renderTimeline(gpx, pointsForTimeline, timelineContainer);
//   } catch (error) {
//     console.error('GPX 解析失敗:', error);
//     timelineContainer.innerHTML = `<p style="color: red;">GPX 檔案解析失敗: ${error.message}</p>`;
//     gpxSummary.style.display = 'none';
//   }
// }

// function sampleTrackPoints(trackPoints, numSamples = 5) {
//   const totalPoints = trackPoints.length;
//   if (totalPoints <= numSamples) return trackPoints.map((p, i) => ({ ...p, name: `軌跡點 ${i + 1}` }));
//   const sampledPoints = [];
//   const indices = new Set([0, totalPoints - 1]);
//   for (let i = 1; i < numSamples - 1; i++) {
//     indices.add(Math.floor(totalPoints * (i / (numSamples - 1))));
//   }
//   [...indices].sort((a, b) => a - b).forEach((index, i) => {
//     const point = trackPoints[index];
//     let name = `路線 ${Math.round((index / totalPoints) * 100)}% 處`;
//     if (i === 0) name = "路線起點";
//     if (i === indices.size - 1) name = "路線終點";
//     sampledPoints.push({ ...point, name: name });
//   });
//   return sampledPoints;
// }

// function renderSummary(gpx, timelinePoints) {
//   const fullTrack = gpx.tracks[0];
//   const totalDistance = (fullTrack?.distance.total / 1000).toFixed(1) || 0;
//   const totalAscent = Math.round(fullTrack?.elevation.pos) || 0;
//   const startTime = new Date(timelinePoints[0].time);
//   const endTime = new Date(timelinePoints[timelinePoints.length - 1].time);
//   const totalMilliseconds = endTime - startTime;
//   const hours = Math.floor(totalMilliseconds / 3600000);
//   const minutes = Math.round((totalMilliseconds % 3600000) / 60000);
//   document.getElementById('total-time').textContent = `${hours} h ${minutes} m`;
//   document.getElementById('total-distance').textContent = `${totalDistance} km`;
//   document.getElementById('total-ascent').textContent = `${totalAscent} m`;
// }

// function renderTimeline(gpx, points, container) {
//   points.forEach((point, index) => {
//     const item = document.createElement('div');
//     item.className = 'timeline-item';
//     const time = new Date(point.time);
//     const formattedTime = `${String(time.getHours()).padStart(2, '0')}:${String(time.getMinutes()).padStart(2, '0')}`;
//     item.innerHTML = `...`;
//     container.appendChild(item);
//     if (index < points.length - 1) {
//     }
//   });
// }