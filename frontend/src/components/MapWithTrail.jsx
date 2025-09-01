import React, { useEffect, useMemo, useImperativeHandle, forwardRef } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap, LayersControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import '../styles/MapWithTrail.css';
import L from 'leaflet'

const cmIcon = L.icon({
  iconUrl: '/icons/cm_marker.svg',
  iconSize: [32, 48],
  iconAnchor: [16, 48],
  popupAnchor: [0, -32],
})

// 調整地圖視圖的組件
function AdjustMapView({ routeFeatures, pointFeatures }) {
  const map = useMap();

  useEffect(() => {
    if (routeFeatures.length > 0 || pointFeatures.length > 0) {
      const bounds = [];

      routeFeatures.forEach(feature => {
        bounds.push(...feature.geometry.coordinates.map(([lng, lat]) => [lat, lng]));
      });

      pointFeatures.forEach(feature => {
        bounds.push([feature.geometry.coordinates[1], feature.geometry.coordinates[0]]);
      });

      if (bounds.length > 0) {
        map.fitBounds(bounds);
      }
    }
  }, [routeFeatures, pointFeatures, map]);

  return null;
}

// MapWithTrail 組件：顯示特定步道的地圖
const MapWithTrail = forwardRef(({ trail, trailId, style = { height: '400px', width: '100%' }, shouldAutoZoom = true, onMapReady }, ref) => {
  const [trailData, setTrailData] = React.useState(null);
  const mapRef = React.useRef();

  useImperativeHandle(ref, () => ({
    getVisibleTiles: () => {
      const map = mapRef.current;
      if (!map) return [];

      const bounds = map.getBounds();
      const zoom = map.getZoom();
      const tiles = [];

      const tileSize = 256;
      const scale = Math.pow(2, zoom);

      const nwTile = {
        x: Math.floor((bounds.getWest() + 180) / 360 * scale),
        y: Math.floor((1 - Math.log(Math.tan(bounds.getNorth() * Math.PI / 180) + 1 / Math.cos(bounds.getNorth() * Math.PI / 180)) / Math.PI) / 2 * scale),
      };

      const seTile = {
        x: Math.floor((bounds.getEast() + 180) / 360 * scale),
        y: Math.floor((1 - Math.log(Math.tan(bounds.getSouth() * Math.PI / 180) + 1 / Math.cos(bounds.getSouth() * Math.PI / 180)) / Math.PI) / 2 * scale),
      };

      for (let x = nwTile.x; x <= seTile.x; x++) {
        for (let y = nwTile.y; y <= seTile.y; y++) {
          tiles.push({ z: zoom, x, y });
        }
      }

      return tiles;
    },
  }));

  // 獲取步道路線資料
  useEffect(() => {
    async function fetchTrailData() {
      const storedTrailData = localStorage.getItem(`trailData_${trailId}`);
      if (storedTrailData) {
        setTrailData(JSON.parse(storedTrailData));
      } else {
        const response = await fetch(`/api/trails/${trailId}`);
        if (response.ok) {
          const data = await response.json();
          setTrailData(data);
          localStorage.setItem(`trailData_${trailId}`, JSON.stringify(data));
        }
      }
    }
    fetchTrailData();
  }, [trailId]);

  const routeFeatures = useMemo(() => {
    return trailData?.features?.filter(f => f.geometry.type === 'LineString') || [];
  }, [trailData]);

  const pointFeatures = useMemo(() => {
    return trailData?.features?.filter(f => f.geometry.type === 'Point') || [];
  }, [trailData]);

  return (
    <MapContainer ref={mapRef} style={style} center={[24.4, 121.3]} zoom={16}>
      <LayersControl position="topright">
        <LayersControl.BaseLayer checked name="OpenStreetMap">
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="等高線圖">
          <TileLayer
            url="https://tile.opentopomap.org/{z}/{x}/{y}.png"
            attribution="Map data: &copy; <a href='https://www.opentopomap.org/'>OpenTopoMap</a> contributors"
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="衛星圖">
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="&copy; ESRI contributors"
          />
        </LayersControl.BaseLayer>
      </LayersControl>
      <AdjustMapView routeFeatures={routeFeatures} pointFeatures={pointFeatures} />
      {routeFeatures.map((feature, index) => (
        <Polyline
          key={index}
          positions={feature.geometry.coordinates.map(([lng, lat]) => [lat, lng])}
          color="#00796b"
          weight={4}
          opacity={0.8}
        />
      ))}
      {pointFeatures.map((feature, index) => (
        <Marker
          key={index}
          position={[feature.geometry.coordinates[1], feature.geometry.coordinates[0]]}
          icon={cmIcon}
        >
          <Popup>
            <div>
              <h4>{feature.properties.name}</h4>
              <p>{feature.properties.description || '無描述'}</p>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
});

export default MapWithTrail;
