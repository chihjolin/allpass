import React from 'react';

// WeatherCard 組件：顯示單一時間點的天氣預報
export default function WeatherCard({ entry }) {
  // 格式化時間（只顯示日期和小時）
  let displayTime = entry.time;
  if (displayTime) {
    const d = new Date(displayTime);
    if (!isNaN(d)) {
      displayTime = `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:00`;
    }
  }

  // pop 欄位容錯
  let popDisplay = 'N/A';
  if (entry.pop !== undefined && entry.pop !== null && entry.pop !== '-' && entry.pop !== 'N/A') {
    popDisplay = entry.pop + '%';
  }

  return (
    <div className="weather-card">
      <h3>{displayTime}</h3>
      <p>🌡️ {entry.temp}°C</p>
      <p>🌧️ 降雨機率：{popDisplay}</p>
      <p>🌤️ 天氣：{entry.wx || 'N/A'}</p>
    </div>
  );
}
