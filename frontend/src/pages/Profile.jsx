import React, { useEffect, useState } from 'react';
import '../styles/Profile.css';
import Navbar from '../components/Navbar';
import TrailCard from '../components/TrailCard';

export default function Profile() {
    const [recommendedTrails, setRecommendedTrails] = useState([]);

    useEffect(() => {
        async function fetchRecommendedTrails() {
            try {
                const res = await fetch('/api/recommended-trails');
                if (!res.ok) throw new Error('Network response was not ok');
                const data = await res.json();
                setRecommendedTrails(data.trails);
            } catch (err) {
                console.error('Failed to fetch recommended trails:', err);
            }
        }

        fetchRecommendedTrails();
    }, []);

    return (
        <>
            <Navbar alwaysScrolled={true} />
            <div className="profile-container">
                <div className="profile-header">
                    <img
                        src="img/dora.png"
                        alt="User Avatar"
                        className="profile-avatar"
                    />
                    <h1 className="profile-username">Dora</h1>
                </div>

                <div className="profile-section">
                    <h2>登山建議報告</h2>
                    <p className="profile-report">
                        本次路線為中級山行程，總長約 9 公里，累積爬升超過 900 公尺。依據地形特徵與氣象資料，本路線屬於「中高挑戰等級」，適合具備一定登山經驗與體能的隊伍進行。

                        首先，路線前半段多為林道與緩坡，適合作為熱身，但需注意部分地段潮濕泥濘，建議穿著具止滑功能的登山鞋。進入中後段後，坡度明顯增加，連續上坡對心肺與腿部肌力有較高要求，隊員應確保能維持穩定步伐，避免急行導致體能消耗過快。依據過往紀錄，平均完登時間約 6–7 小時，若攜帶大背包或遇上天氣不佳，時間可能延長至 8 小時以上。

                        氣象部分，根據近期預測，午後山區可能有短暫雷陣雨。建議於上午早些出發，以降低午後天氣不穩定的風險。請務必攜帶雨具與防水背包套，並準備一套乾燥衣物，以免因淋雨造成失溫風險。山區氣溫落差大，即便夏季日間炎熱，夜間仍可能低至 10–12 度，建議攜帶輕量保暖衣物。

                        安全方面，路線中段有數處崩塌邊坡與窄稜，通過時務必專注腳步，並保持隊伍間適當間距。若近期降雨，需特別注意落石與路徑濕滑。強烈建議攜帶頭盔、登山杖，以及基本急救裝備。

                        補給部分，沿途缺乏穩定水源，僅少數溪流可取水，建議至少攜帶 2–3 公升飲水，並備有濾水裝置或淨水錠。同時，應攜帶高熱量行動糧，如能量棒、堅果、巧克力等，以補充長時間行進所需能量。

                        最後，請事先規劃撤退點與替代方案，並將行程告知家人或友人。若有隊員出現高山症或嚴重疲勞，務必果斷折返。登山是一場與自然的協商，保持謹慎與彈性，才能確保安全與愉快的山行體驗。
                    </p>
                </div>

                <div className="profile-section">
                    <h2>過往登山紀錄</h2>
                    <ul className="profile-records">
                        <li>2025-08-01 玉山主峰</li>
                        <li>2025-07-15 合歡山北峰</li>
                        <li>2025-06-20 桃山瀑布</li>
                    </ul>
                </div>

                <div className="profile-section">
                    <h2>你可能會喜歡</h2>
                    <div className="trail-recommendations">
                        {recommendedTrails.map(trail => (
                            <TrailCard key={trail.id} trail={trail} />
                        ))}
                    </div>
                </div>
            </div>
        </>
    );
}
