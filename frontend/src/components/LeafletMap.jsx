import React, { useEffect, useRef } from 'react';

// LeafletMap 組件：封裝 Leaflet 地圖功能為 React 組件
export default function LeafletMap({
  id = 'leaflet-map',
  center = null,
  zoom = null,
  style = null,
  onMapReady = null,
  enableGPX = false,
  gpxFile = null,
  onGPXLoaded = null
}) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const gpxLayerRef = useRef(null);

  // 初始化地圖
  useEffect(() => {
    if (!mapRef.current) return;

    // 動態導入 Leaflet
    import('leaflet').then((L) => {
      // 修復 Leaflet 圖標問題
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: '/libs/leaflet/images/marker-icon-2x.png',
        iconUrl: '/libs/leaflet/images/marker-icon.png',
        shadowUrl: '/libs/leaflet/images/marker-shadow.png',
      });

      if (mapRef.current && mapRef.current._leaflet_id) {
        mapRef.current._leaflet_id = null;
      }

      // 創建地圖實例
      const map = L.map(mapRef.current).setView(center, zoom);

      // 添加 OpenStreetMap 圖磚
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);

      mapInstanceRef.current = map;

      // 調用回調函數，讓父組件可以獲取地圖實例
      if (onMapReady) {
        onMapReady(map);
      }
    });

    // 清理函數
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [center, zoom, onMapReady]);

  // 處理 GPX 文件加載
  useEffect(() => {
    if (!enableGPX || !gpxFile || !mapInstanceRef.current) return;

    // 移除舊的 GPX 圖層
    if (gpxLayerRef.current) {
      mapInstanceRef.current.removeLayer(gpxLayerRef.current);
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        // 動態導入 GPX 插件
        if (window.L && window.L.GPX) {
          const gpxLayer = new window.L.GPX(event.target.result, {
            async: true,
            marker_options: {
              startIconUrl: '/libs/leaflet/images/icon_blue.png',
              shadowUrl: '/libs/leaflet/images/marker-shadow.png',
              endIconUrl: '/libs/leaflet/images/icon_red.png'
            }
          });

          gpxLayer.on('loaded', (e) => {
            mapInstanceRef.current.fitBounds(e.target.getBounds());
            if (onGPXLoaded) {
              onGPXLoaded(e.target);
            }
          });

          gpxLayer.addTo(mapInstanceRef.current);
          gpxLayerRef.current = gpxLayer;
        }
      } catch (error) {
        console.error('Error loading GPX file:', error);
      }
    };

    reader.readAsText(gpxFile);
  }, [gpxFile, enableGPX, onGPXLoaded]);

  return <div ref={mapRef} id={id} style={style} />;
}
