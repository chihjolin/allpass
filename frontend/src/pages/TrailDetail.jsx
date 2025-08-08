import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import StatsGrid from '../components/StatsGrid';
import WeatherCard from '../components/WeatherCard';
import MapWithTrail from '../components/MapWithTrail';

// TrailDetail 組件：顯示單一步道的詳細資訊與天氣預報
export default function TrailDetail() {
  const { id } = useParams(); // 從 URL 取得步道 id
  const [trail, setTrail] = useState(null); // 步道詳細資料
  const [weather, setWeather] = useState([]); // 天氣預報陣列
  const [error, setError] = useState(null); // 錯誤訊息

  useEffect(() => {
    async function load() {
      try {
        // 向後端取得步道詳細資料
        const trailRes = await fetch(`/api/trails/${id}`);
        if (!trailRes.ok) throw new Error('Trail not found');
        const trailData = await trailRes.json();
        setTrail(trailData);

        // 取得天氣預報資料
        const weatherRes = await fetch(`/api/weather/${trailData.weatherStation.locationName}`);
        if (!weatherRes.ok) throw new Error('無法取得天氣資料');
        const weatherData = await weatherRes.json();
        setWeather(weatherData);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
  }, [id]);

  // if (error) {
  //   return <p>載入步道資料時發生錯誤：{error}</p>;
  // }

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
            <Link to={`/plan/${trail.id}`} className="cta-button">
              <i className="fa-solid fa-calculator"></i> 路線時間規劃
            </Link>
          </div>
          <StatsGrid trail={trail} />
        </section>
        <section className="map-section">
          <h2>步道位置</h2>
          <MapWithTrail trail={trail} style={{ height: '400px', width: '100%' }} />
        </section>
        <section className="weather-section">
          <h2>每小時天氣預報</h2>
          <div className="weather-hourly-forecast">
            {weather.map((entry, idx) => (
              <WeatherCard key={idx} entry={entry} />
            ))}
          </div>
        </section>
      </main>
      <footer>
        <p>&copy; 2025 登山資訊網. All rights reserved.</p>
      </footer>
    </>
  );
}
