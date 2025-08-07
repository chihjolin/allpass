import React from 'react';

// StatsGrid 組件：顯示步道的統計資訊
// 接收 trail 物件，從中取出 stats 與其他屬性
export default function StatsGrid({ trail }) {
  const stats = trail.stats || {};
  return (
    <div className="stats-grid">
      <div className="stat-item">
        <i className="fa-solid fa-clock"></i>
        <div className="label">總時間</div>
        <div className="value">{stats.totalTime}</div>
      </div>
      <div className="stat-item">
        <i className="fa-solid fa-route"></i>
        <div className="label">總移動距離</div>
        <div className="value">{stats.distance}</div>
      </div>
      <div className="stat-item">
        <i className="fa-solid fa-arrow-trend-up"></i>
        <div className="label">總爬升高度</div>
        <div className="value">{stats.ascent}</div>
      </div>
      <div className="stat-item">
        <i className="fa-solid fa-arrow-trend-down"></i>
        <div className="label">總下降高度</div>
        <div className="value">{stats.descent}</div>
      </div>
      <div className="stat-item">
        <i className="fa-solid fa-layer-group"></i>
        <div className="label">難易度</div>
        <div className="value">{trail.difficulty}</div>
      </div>
      <div className="stat-item">
        <i className="fa-solid fa-id-card"></i>
        <div className="label">申請入山</div>
        <div className="value">{trail.permitRequired ? '是' : '否'}</div>
      </div>
    </div>
  );
}
