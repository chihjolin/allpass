import React from 'react';

// StatsGrid 組件：顯示步道的統計資訊
// 接收 trail 物件，從中取出 stats 與其他屬性
export default function StatsGrid({ trail }) {
  return (
    <div className="stats-grid">
      <div className="stat-item">
        <i className="fa-solid fa-id-card"></i>
        <div className="label">申請入山</div>
        <div className="value">{trail.permitRequired ? '是' : '否'}</div>
      </div>
      <div className="stat-item">
        <i className="fa-solid fa-ruler-horizontal"></i>
        <div className="label">步道長度</div>
        <div className="value">{trail.length_km}</div>
      </div>
      <div className="stat-item">
        <i className="fa-solid fa-mountain"></i>
        <div className="label">起始海拔</div>
        <div className="value">{trail.elevation_start_m}</div>
      </div>
      <div className="stat-item">
        <i className="fa-solid fa-mountain"></i>
        <div className="label">最高海拔</div>
        <div className="value">{trail.elevation_end_m}</div>
      </div>
      <div className="stat-item">
        <i className="fa-solid fa-cloud"></i>
        <div className="label">最近氣象站</div>
        <div className="value">{trail.weatherStation?.[0]?.name || '無'}</div>
      </div>
    </div>
  );
}
