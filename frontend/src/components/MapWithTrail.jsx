import React from 'react';
import LeafletMap from '../components/LeafletMap';

// MapWithTrail 組件：顯示特定步道的地圖
export default function MapWithTrail({ trail, style = { height: '400px', width: '100%' } }) {
  const handleMapReady = (map) => {
    if (trail && trail.coordinates) {
      // 動態導入 Leaflet 來創建標記
      import('leaflet').then((L) => {
        // 如果步道有座標資訊，設置地圖中心
        const { lat, lng } = trail.coordinates;
        map.setView([lat, lng], 14);
        
        // 添加步道標記
        const marker = L.marker([lat, lng]).addTo(map);
        marker.bindPopup(`
          <div>
            <h3>${trail.name}</h3>
            <p>${trail.location}</p>
            <p>難度: ${trail.difficulty}</p>
            <p>距離: ${trail.distance}</p>
          </div>
        `);
      });
    }
  };

  return (
    <LeafletMap
      center={trail?.coordinates ? [trail.coordinates.lat, trail.coordinates.lng] : [24, 121]}
      zoom={14}
      style={style}
      onMapReady={handleMapReady}
    />
  );
}
