import React, { useState, useEffect } from 'react';
import LeafletMap from '../components/LeafletMap';

// MapWithTrail 組件：顯示特定步道的地圖
export default function MapWithTrail({ trail, trailId, style = { height: '400px', width: '100%' }, shouldAutoZoom = true, onMapReady }) {
  const [trailData, setTrailData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 獲取步道路線資料
  useEffect(() => {
    if (!trailId && !trail) return;

    const fetchTrailData = async () => {
      try {
        setLoading(true);
        const id = trailId || trail?.id;
        if (!id) return;

        // 獲取步道詳細資料（包含路線和標記點）
        const trailResponse = await fetch(`/api/trails/${id}`);
        if (!trailResponse.ok) {
          throw new Error(`獲取步道資料失敗: ${trailResponse.status}`);
        }
        const trailData = await trailResponse.json();
        setTrailData(trailData);

        // 將步道資料存儲到 localStorage 供 PredictBtn 使用
        localStorage.setItem(`trailData_${id}`, JSON.stringify(trailData));

        setError(null);
      } catch (err) {
        console.error('Error fetching trail data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTrailData();
  }, [trailId, trail?.id]);

  const handleMapReady = (map) => {
    // 動態導入 Leaflet 來創建標記
    import('leaflet').then((L) => {
      // 設置地圖初始中心點
      let centerLat = 24.4;
      let centerLng = 121.3;
      let hasTrailData = false;

      // 處理步道路線資料
      if (trailData && trailData.features) {
        const routeFeatures = [];
        const pointFeatures = [];

        trailData.features.forEach((feature) => {
          if (feature.geometry.type === 'LineString') {
            routeFeatures.push(feature);
          } else if (feature.geometry.type === 'Point') {
            pointFeatures.push(feature);
          }
        });

        // 繪製路線
        routeFeatures.forEach((feature) => {
          const coordinates = feature.geometry.coordinates.map(coord => [coord[1], coord[0]]);
          L.polyline(coordinates, {
            color: '#00796b',
            weight: 4,
            opacity: 0.8
          }).addTo(map).bindPopup(`
            <div>
              <h4>${feature.properties.name}</h4>
              <p>步道路線</p>
              <p>難度: ${feature.properties.difficulty}</p>
              <p>距離: ${feature.properties.stats?.distance}</p>
            </div>
          `);

          // 設置地圖中心為路線中點
          if (coordinates.length > 0) {
            const midIndex = Math.floor(coordinates.length / 2);
            centerLat = coordinates[midIndex][0];
            centerLng = coordinates[midIndex][1];
            hasTrailData = true;
          }
        });

        // 繪製標記點（使用後端回傳的 Point 資料）
        const markers = [];
        pointFeatures.forEach((feature) => {
          const [lng, lat] = feature.geometry.coordinates;
          const marker = L.marker([lat, lng]).addTo(map);

          marker.bindPopup(`
            <div>
              <h4>${feature.properties.name}</h4>
              <p>類型: ${feature.properties.type}</p>
              <p>${feature.properties.description || ''}</p>
              <p>座標: ${lat.toFixed(5)}, ${lng.toFixed(5)}</p>
            </div>
          `);

          markers.push(marker);
        });

        // 調整地圖視野以包含所有路線和標記點
        if (routeFeatures.length > 0 || markers.length > 0) {
          const allFeatures = [
            ...routeFeatures.map(f => {
              return f.geometry.coordinates.map(coord => [coord[1], coord[0]]);
            }).flat(),
            ...markers.map(m => m.getLatLng())
          ];

          if (allFeatures.length > 1) {
            const bounds = L.latLngBounds(allFeatures);
            if (shouldAutoZoom) {
              map.fitBounds(bounds.pad(0.1));
            }
          } else if (allFeatures.length === 1) {
            if (shouldAutoZoom) {
              map.setView(allFeatures[0], 14);
            }
          }
        }

        hasTrailData = routeFeatures.length > 0 || pointFeatures.length > 0;
      }

      // 如果沒有步道資料，設置預設地圖中心
      if (!hasTrailData) {
        map.setView([centerLat, centerLng], 12);
      }

      // 如果有傳入的 trail 資料，也添加該標記（用於向下相容）
      if (trail && trail.coordinates && !trailId) {
        const { lat, lng } = trail.coordinates;
        const trailMarker = L.marker([lat, lng], {
          icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
          })
        }).addTo(map);

        trailMarker.bindPopup(`
          <div>
            <h3>${trail.name}</h3>
            <p>${trail.location}</p>
            <p>難度: ${trail.difficulty}</p>
            <p>距離: ${trail.distance}</p>
          </div>
        `);
      }

      // 調用地圖準備完成的回調
      if (onMapReady) {
        onMapReady();
      }
    });
  };

  if (loading) {
    return (
      <div style={{ ...style, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div>載入地圖資料中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ ...style, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'red' }}>載入地圖資料失敗: {error}</div>
      </div>
    );
  }

  return (
    <LeafletMap
      center={[24.4, 121.3]}
      zoom={12}
      style={style}
      onMapReady={handleMapReady}
    />
  );
}
