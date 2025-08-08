import React, { useEffect, useState } from 'react';
import TrailCard from '../components/TrailCard';
import { useNavigate } from 'react-router-dom';

// Home 組件：負責載入並顯示所有步道卡片
export default function Home() {
  const [trails, setTrails] = useState([]); // 存放步道陣列
  const [error, setError] = useState(null); // 錯誤訊息
  const navigate = useNavigate();

  // 元件掛載後向後端取得步道資料
  useEffect(() => {
    async function fetchTrails() {
      try {
        const res = await fetch('/api/trails');
        if (!res.ok) throw new Error('Network response was not ok');
        const json = await res.json();
        setTrails(json.trails);
      } catch (err) {
        // 將錯誤訊息記錄於 state 以便顯示在畫面上
        setError(err.message);
      }
    }
    fetchTrails();
  }, []);

  // 處理步道卡片點擊
  const handleTrailClick = (trail) => {
    // 將選擇的步道資料存儲到 localStorage
    localStorage.setItem('selectedTrail', JSON.stringify({
      id: trail.id,
      name: trail.name,
      location: trail.location,
      difficulty: trail.difficulty,
      permitRequired: trail.permitRequired,
      selectedAt: new Date().toISOString()
    }));
    
    // 導航到步道詳細頁面
    navigate(`/trail/${trail.id}`);
  };

  if (error) {
    return <p>無法載入步道列表：{error}</p>;
  }

  return (
    <>
      <header>
        <h1>探索台灣步道</h1>
        <p>選擇一條步道，開始您的旅程</p>
      </header>
      <main>
        <div className="trail-grid">
          {trails.map(trail => (
            <TrailCard
              key={trail.id}
              trail={trail}
              onClick={() => handleTrailClick(trail)}
            />
          ))}
        </div>
      </main>
      <footer>
        <p>&copy; 2025 登山資訊網. All rights reserved.</p>
      </footer>
    </>
  );
}
