import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import TrailDetail from './pages/TrailDetail';
import PlanPage from './pages/PlanPage';
import './components/Navbar.css'; // 引入 Navbar 樣式

// App 組件負責定義前端的路由
export default function App() {
  return (
    <>
      <Routes>
        {/* 首頁：步道列表 */}
        <Route path="/" element={<Home />} />
        {/* 步道詳情頁：使用動態參數 id */}
        <Route path="/trail/:id" element={<TrailDetail />} />
        {/* 路線規劃頁 */}
        <Route path="/plan/:id" element={<PlanPage />} />
      </Routes>
    </>
  );
}
