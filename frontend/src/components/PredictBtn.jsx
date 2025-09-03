import React, { useState } from 'react';

/**
 * PredictBtn 組件
 * 點擊按鈕時，使用 localStorage 中的步道資料逐步更新時間軸預測
 * @param {function} onResult - 回傳後端結果的 callback
 * @param {string} trailId - 步道 ID
 * @param {Object} currentTimelineData - 當前的時間軸資料
 */
export default function PredictBtn({ onResult, trailId, currentTimelineData }) {
    const [currentIndex, setCurrentIndex] = useState(0); // 用於追蹤當前處理的點索引
    const [timeline, setTimeline] = useState([]); // 用於存儲已處理的時間軸數據

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

            if (currentIndex >= pointFeatures.length) {
                if (onResult) onResult({
                    success: true,
                    message: '所有點已處理完成',
                    timeline: timeline
                });
                return;
            }

            const point = pointFeatures[currentIndex];
            const { id, order, name } = point.properties;

            // 獲取當下的時間
            const time = new Date().toISOString();


            try {
                const res = await fetch('/api/predictions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        trailId: trailId,
                        id,
                        order,
                        time, // 將當下的時間加入到 POST 請求的 body 中
                        user_id: localStorage.getItem('user_id')
                    })
                });

                // console.log("要傳送的 data:", {
                //     trailId: trailId,
                //     id,
                //     order,
                //     time,
                //     user_id: localStorage.getItem('user_id')
                // });

                // if (!res.ok) {
                //     throw new Error(`API 請求失敗: ${res.status}`);
                // }

                // const apiResult = await res.json();

                // 建立當前點的 timeline 項目
                const baseTime = new Date();
                baseTime.setHours(6, 0, 0, 0);
                const timeOffset = currentIndex * (60 + Math.random() * 60); // 每點間隔 1-2 小時
                const displayTime = new Date(baseTime.getTime() + timeOffset * 60000);
                const existingPoint = currentTimelineData?.timeline?.[currentIndex];

                const newTimelineItem = {
                    id: currentIndex + 1,
                    name: name || `標記點 ${currentIndex + 1}`,
                    time: displayTime.toTimeString().slice(0, 5),
                    elevation: existingPoint?.elevation || Math.floor(Math.random() * 500 + 100),
                    distanceFromPrev: existingPoint?.distanceFromPrev || (currentIndex > 0 ? Math.round((1.5 + Math.random() * 1.5) * 10) / 10 : 0),
                    timeFromPrev: currentIndex > 0 ? Math.round((60 + Math.random() * 60)) : 0,
                    type: currentIndex === 0 ? 'start' : (currentIndex === pointFeatures.length - 1 ? 'end' : 'waypoint'),
                    originalPoint: point,
                    predicted: true,
                    // apiResponse: apiResult // 每個點的 API 結果也存起來
                };

                // 更新 timeline 狀態
                setTimeline(prevTimeline => [...prevTimeline, newTimelineItem]);

                // 回傳當前點的結果
                if (onResult) onResult({
                    success: true,
                    timeline: [...timeline, newTimelineItem],
                    currentPoint: newTimelineItem
                });

                // 更新索引到下一個點
                setCurrentIndex(currentIndex + 1);

            } catch (err) {
                console.error(`點 ${id} 預測失敗:`, err);
                if (onResult) onResult({
                    error: true,
                    message: `點 ${id} 預測失敗`,
                    details: err.message
                });
            }
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