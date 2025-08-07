import React from 'react';
import { Link } from 'react-router-dom';

// TrailCard 組件：顯示單一步道的名稱、地點與難易度
// props.trail 為後端 API 回傳的一筆步道資料
export default function TrailCard({ trail }) {
  return (
    <Link to={`/trail/${trail.id}`} className="trail-card">
      <div className="card-content">
        <h3>{trail.name}</h3>
        <p><i className="fa-solid fa-map-marker-alt"></i> {trail.location}</p>
        <p><strong>難易度:</strong> {trail.difficulty}</p>
      </div>
    </Link>
  );
}
