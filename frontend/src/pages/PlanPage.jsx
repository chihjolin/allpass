import React, { useRef, useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import LeafletMap from '../components/LeafletMap';

import PredictBtn from '../components/PredictBtn';

// PlanPage 組件：提供 GPX 檔案上傳與地圖展示功能
export default function PlanPage() {
  const { id } = useParams(); // 取得步道 id，方便返回詳情頁
  const mapRef = useRef(null); // 地圖實例引用
  const [routeGeoJson, setRouteGeoJson] = useState(null); // 標準路線
  const [waypoints, setWaypoints] = useState([]); // 通訊點座標
  const [selectedGPX, setSelectedGPX] = useState(null);

  // 地圖初始化回調
  const handleMapReady = (map) => {
    mapRef.current = map;
  };

  // 監聽 routeGeoJson/waypoints 變化，渲染到地圖
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !window.L) return;
    // 清理舊圖層
    if (map._routeLayer) {
      map.removeLayer(map._routeLayer);
      map._routeLayer = null;
    }
    if (map._waypointLayers) {
      map._waypointLayers.forEach(marker => map.removeLayer(marker));
      map._waypointLayers = null;
    }
    // 加入新路線
    if (routeGeoJson) {
      const coords = routeGeoJson.geometry.coordinates.map(coord => [coord[1], coord[0]]);
      map._routeLayer = window.L.polyline(coords, { color: '#00796b', weight: 5 }).addTo(map);
    }
    // 加入新通訊點
    if (waypoints && waypoints.length > 0) {
      map._waypointLayers = waypoints.map(pt => {
        const [lng, lat] = pt.geometry.coordinates;
        return window.L.marker([lat, lng], {
          title: pt.properties.label
        }).addTo(map).bindPopup(pt.properties.label);
      });
    }
  }, [routeGeoJson, waypoints]);

  // GPX 加載完成回調
  const handleGPXLoaded = (gpxLayer) => {
    console.log('GPX loaded successfully', gpxLayer);
  };

  // 取得後端 API 路線與通訊點
  useEffect(() => {
    async function fetchRoute() {
      const res = await fetch(`/api/trail/${id}/route`);
      const data = await res.json();
      // 取出 LineString 作為 route，Point 作為 waypoints
      const route = data.features?.find(f => f.geometry.type === 'LineString');
      const points = data.features?.filter(f => f.geometry.type === 'Point') || [];
      setRouteGeoJson(route);
      setWaypoints(points);
    }
    fetchRoute();
  }, [id]);


  // 處理 PredictBtn 回傳
  function handleGPXResult(result) {
    const display = document.getElementById('gpx-timeline-display');
    if (result?.error) {
      display.innerHTML = '<p style="color:red;">分析失敗。</p>';
    } else {
      display.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
    }
  }

  return (
    <>
      <header className="trail-header plan-header">
        <Link to={`/trail/${id}`} className="back-link plan-back-link"><i className="fa-solid fa-arrow-left"></i> 返回詳情</Link>
        <h1 id="plan-trail-name" className="plan-title">路線規劃與分析</h1>
      </header>
      <div className="plan-flex-layout">
        {/* Sidebar: GPX 時間軸分析 */}
        <aside className="plan-sidebar">
          <h2 className="plan-sidebar-title">GPX 時間軸分析</h2>
          <div className="plan-gpx-upload">
            <PredictBtn onResult={handleGPXResult} />
          </div>
          <div id="gpx-timeline-display" className="gpx-timeline-display plan-timeline-display"></div>
        </aside>
        {/* Main map area */}
        <div className="plan-map-area">
          <LeafletMap
            id="map_plan"
            center={[24.39700, 121.30770]}
            zoom={14}
            style={{ height: '100%', width: '100%', borderRadius: 0, boxShadow: 'none' }}
            enableGPX={false}
            onMapReady={handleMapReady}
            onGPXLoaded={handleGPXLoaded}
          />
        </div>
      </div>
    </>
  );
}
