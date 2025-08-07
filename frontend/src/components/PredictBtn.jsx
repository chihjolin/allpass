import React from 'react';

/**
 * GPXUploadButton 組件
 * 點擊按鈕時，將當下時間（ISO字串）POST 給 /api/gpxanalyzer
 * 無檔案選擇功能，僅回傳時間
 * @param {function} onResult - 回傳後端結果的 callback
 */
export default function PredictBtn({ onResult }) {
    const handleClick = async () => {
        const now = new Date();
        const localTime = now.toLocaleString('sv-SE', { timeZone: 'Asia/Taipei' });
        try {
            const res = await fetch('/api/time', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ timestamp: localTime })
            });
            const result = await res.json();
            if (onResult) onResult(result);
        } catch (err) {
            if (onResult) onResult({ error: true, message: '分析失敗' });
        }
    };

    return (
        <button className="cta-button plan-gpx-btn" onClick={handleClick}>
            回傳時間
        </button>
    );
}
