import React from 'react';
import './TimelineDisplay.css';

/**
 * TimelineDisplay 組件
 * 顯示步道時間軸預測結果
 * @param {Object} timelineData - 時間軸資料
 */
export default function TimelineDisplay({ timelineData }) {
    if (!timelineData) {
        return (
            <div className="timeline-placeholder">
                <i className="fa-solid fa-clock"></i>
                <p>載入步道資料中...</p>
            </div>
        );
    }

    if (timelineData.loading) {
        return (
            <div className="timeline-placeholder">
                <i className="fa-solid fa-spinner fa-spin"></i>
                <p>{timelineData.message || '載入步道資料中...'}</p>
            </div>
        );
    }

    if (timelineData.error) {
        return (
            <div className="timeline-error">
                <p style={{ color: 'red' }}>
                    <i className="fa-solid fa-exclamation-triangle"></i> {timelineData.message}
                </p>
                {timelineData.details && (
                    <p style={{ fontSize: '0.9em', color: '#666' }}>{timelineData.details}</p>
                )}
            </div>
        );
    }

    const { timeline } = timelineData;

    // 格式化時間（分鐘轉換為小時分鐘）
    const formatDuration = (minutes) => {
        if (minutes === 0) return '';
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        if (hours === 0) return `${mins} m`;
        if (mins === 0) return `${hours} h`;
        return `${hours} h ${mins} m`;
    };

    return (
        <div className="timeline-container">
            {timeline.map((point, index) => (
                <div key={point.id} className="timeline-item">
                    {/* 時間點圓圈 */}
                    <div className="timeline-point">
                        <div className={`timeline-circle ${!point.predicted ? 'unpredicted' : ''}`}>
                            <span className="timeline-number">{point.id}</span>
                        </div>
                        <div className={`timeline-time ${!point.predicted ? 'unpredicted' : ''}`}>
                            {point.time}
                        </div>
                    </div>

                    {/* 地點資訊 */}
                    <div className="timeline-content">
                        <div className="timeline-location">
                            <h4>{point.name}</h4>
                            <span className="timeline-elevation">H {point.elevation} m</span>
                        </div>
                    </div>

                    {/* 連接線和區間資訊 */}
                    {index < timeline.length - 1 && (
                        <div className="timeline-connector">
                            <div className="timeline-line"></div>
                            {point.predicted && timeline[index + 1].timeFromPrev > 0 && (
                                <div className="timeline-segment">
                                    <div className="segment-duration">
                                        {formatDuration(timeline[index + 1].timeFromPrev)}
                                    </div>
                                    <div className="segment-distance">
                                        {timeline[index + 1].distanceFromPrev} km
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}
