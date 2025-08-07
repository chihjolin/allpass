import React from 'react';

// WeatherCard 組件：顯示單一時間點的天氣預報
export default function WeatherCard({ entry }) {
  return (
    <div className="weather-card">
      <h3>{entry.time}</h3>
      <p>🌡️ {entry.temp}°C</p>
      <p>🌧️ 降雨機率：{entry.pop === '-' ? 'N/A' : entry.pop + '%'}</p>
      <p>🌤️ 天氣：{entry.wx}</p>
    </div>
  );
}
