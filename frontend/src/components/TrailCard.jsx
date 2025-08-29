import React from 'react';

// TrailCard 組件：顯示單一步道的名稱、地點
// props.trail 為後端 API 回傳的一筆步道資料
// props.onClick 為點擊卡片時的回調函數
export default function TrailCard({ trail, onClick }) {
  const handleClick = (e) => {
    e.preventDefault();
    if (onClick) {
      onClick(trail);
    }
  };

  return (
    <div className="trail-card" onClick={handleClick} style={{ cursor: 'pointer' }}>
      <div className="card-content">
        <h3>{trail.name}</h3>
        <p><i className="fa-solid fa-map-marker-alt"></i> {trail.location}</p>
        <p><strong>{trail.permitRequired ? '需入園許可證' : '無需許可證'}</strong></p>
      </div>
    </div>
  );
}
