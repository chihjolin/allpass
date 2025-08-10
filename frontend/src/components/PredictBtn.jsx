import React from 'react';

/**
 * PredictBtn 組件
 * 點擊按鈕時，使用 localStorage 中的步道資料更新時間軸預測
 * @param {function} onResult - 回傳後端結果的 callback
 * @param {string} trailId - 步道 ID
 * @param {Object} currentTimelineData - 當前的時間軸資料
 */
export default function PredictBtn({ onResult, trailId, currentTimelineData }) {
    const handleClick = async () => {
        if (!trailId) {
            if (onResult) onResult({
                error: true,
                message: '步道 ID 不存在'
            });
            return;
        }

        try {
            // 從 localStorage 獲取步道資料
            const storedTrailData = localStorage.getItem(`trailData_${trailId}`);

            if (!storedTrailData) {
                if (onResult) onResult({
                    error: true,
                    message: '找不到步道資料，請重新載入頁面'
                });
                return;
            }

            const trailData = JSON.parse(storedTrailData);

            // 提取 Point 類型的 features
            const pointFeatures = trailData.features?.filter(f => f.geometry.type === 'Point') || [];

            if (pointFeatures.length === 0) {
                if (onResult) onResult({
                    error: true,
                    message: '此步道沒有標記點資料'
                });
                return;
            }

            // 模擬時間預測（未來會替換為真實的機器學習預測）
            // 發送時間戳到後端（目前的 API）
            const now = new Date();
            const localTime = now.toLocaleString('sv-SE', { timeZone: 'Asia/Taipei' });

            const res = await fetch('/api/time', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    timestamp: localTime,
                    trailId: trailId,
                    pointCount: pointFeatures.length
                })
            });

            if (!res.ok) {
                throw new Error(`API 請求失敗: ${res.status}`);
            }

            const apiResult = await res.json();

            // 生成基於實際 Point 資料的時間軸，保持現有的地點資訊
            const existingTimeline = currentTimelineData?.timeline || [];
            const timeline = pointFeatures.map((point, index) => {
                // 模擬時間計算：每個點間隔約 1-2 小時
                const baseTime = new Date();
                baseTime.setHours(6, 0, 0, 0); // 從早上6點開始
                const timeOffset = index * (60 + Math.random() * 60); // 1-2小時間隔
                const currentTime = new Date(baseTime.getTime() + timeOffset * 60000);

                // 模擬距離和時間間隔
                const prevTimeOffset = index > 0 ? (index - 1) * (60 + Math.random() * 60) : 0;
                const timeFromPrev = index > 0 ? timeOffset - prevTimeOffset : 0;

                // 保留現有資料或使用新的模擬資料
                const existingPoint = existingTimeline[index];

                return {
                    id: index + 1,
                    name: point.properties.name || `標記點 ${index + 1}`,
                    time: currentTime.toTimeString().slice(0, 5), // HH:MM 格式 - 這是更新的部分
                    elevation: existingPoint?.elevation || Math.floor(Math.random() * 500 + 100),
                    distanceFromPrev: existingPoint?.distanceFromPrev || (index > 0 ? Math.round((1.5 + Math.random() * 1.5) * 10) / 10 : 0),
                    timeFromPrev: Math.round(timeFromPrev), // 這是更新的部分
                    type: index === 0 ? 'start' : (index === pointFeatures.length - 1 ? 'end' : 'waypoint'),
                    originalPoint: point,
                    predicted: true // 標記為已預測狀態
                };
            });

            const timelineData = {
                success: true,
                startTime: timeline[0]?.time || '06:00',
                timeline: timeline,
                trailId: trailId,
                pointCount: pointFeatures.length,
                predicted: true, // 標記為已預測狀態
                apiResponse: apiResult // 保留原始 API 回應
            };

            if (onResult) onResult(timelineData);

        } catch (err) {
            console.error('預測時間軸失敗:', err);
            if (onResult) onResult({
                error: true,
                message: '預測失敗',
                details: err.message
            });
        }
    };

    return (
        <button className="cta-button plan-gpx-btn" onClick={handleClick}>
            <i className="fa-solid fa-route"></i> 預測時間
        </button>
    );
}
