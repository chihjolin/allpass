import React, { useRef, useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import MapWithTrail from '../components/MapWithTrail';
import PredictBtn from '../components/PredictBtn';
import TimelineDisplay from '../components/TimelineDisplay';

// PlanPage 組件：提供 GPX 檔案上傳與地圖展示功能
export default function PlanPage() {
  const { id } = useParams(); // 取得步道 id，方便返回詳情頁
  const [selectedTrail, setSelectedTrail] = useState(null); // 從 localStorage 取得的選擇步道
  const [trailName, setTrailName] = useState('路線規劃與分析');
  const [timelineData, setTimelineData] = useState(null); // 時間軸資料
  const [mapInitialized, setMapInitialized] = useState(false); // 記錄地圖是否已初始化

  useEffect(() => {
    // 從 localStorage 取得選擇的步道資料
    const storedTrail = localStorage.getItem('selectedTrail');
    if (storedTrail) {
      try {
        const parsedTrail = JSON.parse(storedTrail);
        setSelectedTrail(parsedTrail);
        setTrailName(`${parsedTrail.name} - 路線規劃與分析`);
      } catch (err) {
        console.error('解析儲存的步道資料失敗:', err);
      }
    }
  }, []);

  // 在頁面載入時生成初始時間軸
  useEffect(() => {
    if (id) {
      generateInitialTimeline(id);
    }
  }, [id]);

  // 生成初始時間軸（不含精確時間預測）
  const generateInitialTimeline = (trailId) => {
    try {
      // 從 localStorage 獲取步道資料
      const storedTrailData = localStorage.getItem(`trailData_${trailId}`);

      if (!storedTrailData) {
        // 如果沒有資料，設置一個等待狀態
        setTimelineData({
          loading: true,
          message: '載入步道資料中...'
        });
        return;
      }

      const trailData = JSON.parse(storedTrailData);
      const pointFeatures = trailData.features?.filter(f => f.geometry.type === 'Point') || [];

      if (pointFeatures.length === 0) {
        setTimelineData({
          error: true,
          message: '此步道沒有標記點資料'
        });
        return;
      }

      // 生成基本時間軸（顯示地點，但時間顯示為 "--:--"）
      const timeline = pointFeatures.map((point, index) => ({
        id: index + 1,
        name: point.properties.name || `標記點 ${index + 1}`,
        time: '--:--', // 初始狀態顯示為 "--:--"
        elevation: Math.floor(Math.random() * 500 + 100),
        distanceFromPrev: index > 0 ? Math.round((1.5 + Math.random() * 1.5) * 10) / 10 : 0,
        timeFromPrev: 0, // 初始狀態不顯示時間
        type: index === 0 ? 'start' : (index === pointFeatures.length - 1 ? 'end' : 'waypoint'),
        originalPoint: point,
        predicted: false // 標記為未預測狀態
      }));

      setTimelineData({
        success: true,
        startTime: '--:--',
        timeline: timeline,
        trailId: trailId,
        predicted: false // 整體標記為未預測狀態
      });

    } catch (err) {
      console.error('生成初始時間軸失敗:', err);
      setTimelineData({
        error: true,
        message: '載入時間軸失敗',
        details: err.message
      });
    }
  };

  // 處理 PredictBtn 回傳
  function handleTimelineResult(result) {
    setTimelineData(result);
  }

  // 處理地圖初始化完成
  function handleMapInitialized() {
    if (!mapInitialized) {
      setMapInitialized(true);
    }
  }

  return (
    <>
      <header className="trail-header plan-header">
        <Link to={`/trail/${id}`} className="back-link plan-back-link">
          <i className="fa-solid fa-arrow-left"></i> 返回詳情
        </Link>
        <h1 id="plan-trail-name" className="plan-title">{trailName}</h1>
      </header>
      <div className="plan-flex-layout">
        {/* Sidebar: GPX 時間軸分析 */}
        <aside className="plan-sidebar">
          <h2 className="plan-sidebar-title">GPX 時間軸分析</h2>
          <div className="plan-gpx-upload">
            <PredictBtn onResult={(result) => {
              handleTimelineResult(result);
            }} trailId={id} currentTimelineData={timelineData} />
          </div>
          <div className="gpx-timeline-display plan-timeline-display">
            <TimelineDisplay timelineData={timelineData} />
          </div>
        </aside>
        {/* Main map area */}
        <div className="plan-map-area">
          <MapWithTrail
            trailId={id}
            style={{ height: '100%', width: '100%', borderRadius: 0, boxShadow: 'none' }}
            shouldAutoZoom={!mapInitialized}
            onMapReady={handleMapInitialized}
          />
        </div>
      </div>
    </>
  );
}
