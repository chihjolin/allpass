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

function displayWeatherForecast(weather){
    try{
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
    } catch(err){
        console.error('天氣資料錯誤：', err);
        const container = document.getElementById('weather');
        container.innerHTML = '<p>無法載入天氣資訊。</p>';

    }
}
/*
function displayWeatherForecast(weather){
    document.getElementById('weather-forecast').textContent = weather.message;
}
*/
/*

// *** 使用客戶端解析 GPX，不再依賴後端 API ***
function handleGpxUpload() {
    const fileInput = document.getElementById('gpx-file-input');
    const resultArea = document.getElementById('gpx-result');

    if (fileInput.files.length === 0) {
        resultArea.innerHTML = '<p style="color: red;">請先選擇一個 GPX 檔案。</p>';
        return;
    }

    const file = fileInput.files[0];
    const reader = new FileReader();

    reader.onload = (e) => {
        try {
            const gpxContent = e.target.result;
            const gpx = new gpxParser(); // 使用 gpx-parser-js
            gpx.parse(gpxContent);

            if (!gpx.tracks || gpx.tracks.length === 0) {
                throw new Error("此 GPX 檔案不包含軌跡 (track) 資料。");
            }

            const track = gpx.tracks[0];
            const distanceKm = (track.distance.total / 1000).toFixed(2);
            const ascentM = Math.round(track.elevation.pos);
            const descentM = Math.round(Math.abs(track.elevation.neg));

            const startTime = new Date(track.points[0].time);
            const endTime = new Date(track.points[track.points.length - 1].time);
            const durationMs = endTime - startTime;
            const hours = Math.floor(durationMs / 3600000);
            const minutes = Math.round((durationMs % 3600000) / 60000);
            const totalTime = `${hours} 小時 ${minutes} 分鐘`;

            // 將結果顯示在畫面上
            resultArea.innerHTML = `
                <h4>您的軌跡分析結果：</h4>
                <div class="stats-grid">
                    <div class="stat-item"><div class="label">總時間</div><div class="value">${totalTime}</div></div>
                    <div class="stat-item"><div class="label">總距離</div><div class="value">${distanceKm} km</div></div>
                    <div class="stat-item"><div class="label">總爬升</div><div class="value">${ascentM} m</div></div>
                    <div class="stat-item"><div class="label">總下降</div><div class="value">${descentM} m</div></div>
                </div>
            `;
        } catch (error) {
            console.error("GPX 分析出錯:", error);
            resultArea.innerHTML = `<p style="color: red;">分析出錯: ${error.message}</p>`;
        }
    };

    reader.onerror = () => {
        resultArea.innerHTML = `<p style="color: red;">讀取檔案失敗。</p>`;
    };

    resultArea.innerHTML = '<p>分析中，請稍候...</p>';
    reader.readAsText(file);
}
*/
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

    // --- 如果有 trailId，才執行原有的時間計算機功能 ---
    // if (trailId) {
    //     try {
    //         const trailRes = await fetch(`/api/trails/${trailId}`);
    //         const trail = await trailRes.json();

    //         document.getElementById('plan-trail-name').textContent = `規劃: ${trail.name}`;

    //         const calculateBtn = document.getElementById('calculate-time-btn');
    //         calculateBtn.addEventListener('click', () => {
    //             // ... (此處省略未變更的計算邏輯) ...
    //         });
    //     } catch (error) {
    //         console.error("無法載入步道資料進行規劃:", error);
    //     }
    // }
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
