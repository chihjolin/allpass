import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { openDB } from 'idb';
import JSZip from 'jszip';
import StatsGrid from '../components/StatsGrid';
import WeatherCard from '../components/WeatherCard';
import MapWithTrail from '../components/MapWithTrail';

// TrailDetail 組件：顯示單一步道的詳細資訊與天氣預報
export default function TrailDetail() {
  const { id } = useParams(); // 從 URL 取得步道 id
  const [trail, setTrail] = useState(null); // 步道詳細資料
  const [weather, setWeather] = useState([]); // 天氣預報陣列
  const [error, setError] = useState(null); // 錯誤訊息
  const [selectedTrail, setSelectedTrail] = useState(null); // 從 localStorage 取得的選擇步道
  const mapRef = useRef();

  useEffect(() => {
    // 從 localStorage 取得選擇的步道資料
    const storedTrail = localStorage.getItem('selectedTrail');
    if (storedTrail) {
      try {
        const parsedTrail = JSON.parse(storedTrail);
        setSelectedTrail(parsedTrail);
      } catch (err) {
        console.error('解析儲存的步道資料失敗:', err);
      }
    }
  }, []);

  useEffect(() => {
    async function load() {
      try {
        // 向後端取得步道詳細資料 (GeoJSON 格式)
        const trailRes = await fetch(`/api/trails/${id}`);
        if (!trailRes.ok) throw new Error('Trail not found');
        const trailData = await trailRes.json();

        // 從 GeoJSON features 中提取步道基本資訊
        const routeFeature = trailData.features?.find(f => f.geometry.type === 'LineString');
        if (routeFeature) {
          const trailInfo = {
            id: routeFeature.properties.id,
            name: routeFeature.properties.name,
            location: routeFeature.properties.location,
            permitRequired: routeFeature.properties.permitRequired,
            length_km: routeFeature.properties.length_km,
            elevation_start_m: routeFeature.properties.elevation_start_m.replace('起始海拔', ''),
            elevation_end_m: routeFeature.properties.elevation_end_m.replace('最高海拔', ''),
            weatherStation: routeFeature.properties.weatherStation, // Add weather station
            geoJsonData: trailData // Full GeoJSON for map
          };
          setTrail(trailInfo);

          // 取得天氣預報資料
          // weatherStation 是陣列，取第一個 name 作為查詢參數
          let station = null;
          if (Array.isArray(trailInfo.weatherStation) && trailInfo.weatherStation.length > 0) {
            station = trailInfo.weatherStation[0];
          } else if (trailInfo.weatherStation) {
            station = trailInfo.weatherStation;
          }
          if (station && station.name) {
            const weatherRes = await fetch(`/api/weather/${station.name}`);
            if (weatherRes.ok) {
              const weatherData = await weatherRes.json();
              setWeather(weatherData);
            }
          }
        }
      } catch (err) {
        setError(err.message);
      }
    }
    load();
  }, [id]);

  async function saveTilesToIndexedDB(zip) {
    const db = await openDB('tiles-db', 1, {
      upgrade(db) {
        db.createObjectStore('tiles');
      },
    });

    const keys = Object.keys(zip.files);

    for (const key of keys) {
      const tileBlob = await zip.files[key].async('blob');
      await db.put('tiles', tileBlob, key);
    }

    console.log('圖磚已保存到 IndexedDB');
  }

  async function handleDownloadTiles(trailId) {
    const visibleTiles = mapRef.current?.getVisibleTiles();

    if (!visibleTiles || visibleTiles.length === 0) {
      alert('無法取得可見圖磚，請稍後再試！');
      return;
    }

    const response = await fetch(`/api/tiles/download`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ tiles: visibleTiles }),
    });

    if (response.ok) {
      const blob = await response.blob();
      const zip = await JSZip.loadAsync(blob);
      await saveTilesToIndexedDB(zip);
      alert('圖磚下載完成，可離線使用！');
    } else {
      const error = await response.json();
      console.error('下載圖磚失敗:', error);
      alert('下載圖磚失敗，請稍後再試！');
    }
  }

  if (error) {
    return <p>載入步道資料時發生錯誤：{error}</p>;
  }

  if (!trail) {
    return <p>載入中...</p>;
  }

  return (
    <>
      <header className="trail-header">
        <Link to="/" className="back-link"><i className="fa-solid fa-arrow-left"></i> 返回列表</Link>
        <h1 id="trail-name">{trail.name}</h1>
        <p id="trail-location">{trail.location}</p>
      </header>
      <main>
        <section className="stats-section">
          <div className="section-header">
            <h2>路線資訊</h2>
            <button
              className="cta-button"
              onClick={() => {
                handleDownloadTiles(id);
              }}
            >
              <Link to={`/plan/${trail.id}`} className='cta-button'>
                <i className="fa-solid fa-calculator"></i> 路線時間規劃
              </Link>
            </button>
          </div>
          <StatsGrid trail={trail} />
        </section>
        <section className="map-section">
          <h2>步道位置</h2>
          <MapWithTrail ref={mapRef} trailId={trail.id} style={{ height: '400px', width: '100%' }} />
        </section>
        <section className="weather-section">
          <h2>天氣預報</h2>
          <div className="weather-hourly-forecast">
            {weather.map((entry, idx) => (
              <WeatherCard key={idx} entry={entry} />
            ))}
          </div>
        </section>
      </main>
      <footer>
        <p style={{ textAlign: 'center' }}>&copy; 2025 登山資訊網. All rights reserved.</p>
      </footer>
    </>
  );
}
