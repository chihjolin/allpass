import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/Profile.css';
import Navbar from '../components/Navbar';
import TrailCard from '../components/TrailCard';

export default function Profile() {
    const [recommendedTrails, setRecommendedTrails] = useState([]);
    const [userRecords, setUserRecords] = useState([]); // 用於存儲用戶登山紀錄
    const [username, setUsername] = useState(null); // 用於存儲用戶名稱
    const [currentPage, setCurrentPage] = useState(1);
    const recordsPerPage = 5;
    const navigate = useNavigate();

    useEffect(() => {
        // 檢查 localStorage 是否有登入資訊
        const storedUsername = localStorage.getItem('username');
        const userId = localStorage.getItem('user_id');

        if (!storedUsername || !userId) {
            // 如果沒有登入，跳轉到登入頁面
            navigate('/login');
        } else {
            setUsername(storedUsername);

            // 呼叫 /api/user-record/:id 獲取用戶登山紀錄
            async function fetchUserRecords() {
                try {
                    const res = await fetch(`/api/user-record/${userId}`);
                    if (!res.ok) throw new Error('Network response was not ok');
                    const data = await res.json();
                    setUserRecords(data.map(record => ({
                        trail_id: record.trail_id,
                        date: record.date,
                        trail_name: record.file_name,
                        length_km: record.length_km
                    })));
                } catch (err) {
                    console.error('Failed to fetch user records:', err);
                }
            }

            fetchUserRecords();
        }
    }, [navigate]);

    // useEffect(() => {
    //     async function fetchRecommendedTrails() {
    //         try {
    //             const res = await fetch('/api/recommended-trails');
    //             if (!res.ok) throw new Error('Network response was not ok');
    //             const data = await res.json();
    //             setRecommendedTrails(data.trails);
    //         } catch (err) {
    //             console.error('Failed to fetch recommended trails:', err);
    //         }
    //     }

    //     fetchRecommendedTrails();
    // }, []);

    const indexOfLastRecord = currentPage * recordsPerPage;
    const indexOfFirstRecord = indexOfLastRecord - recordsPerPage;
    const currentRecords = userRecords.slice(indexOfFirstRecord, indexOfLastRecord);
    const totalPages = Math.ceil(userRecords.length / recordsPerPage);

    const handleNextPage = () => {
        if (currentPage < totalPages) {
            setCurrentPage(currentPage + 1);
        }
    };

    const handlePrevPage = () => {
        if (currentPage > 1) {
            setCurrentPage(currentPage - 1);
        }
    };

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
                    <h1 className="profile-username">{username}</h1>
                </div>

                <div className="profile-section">
                    <h2>個人統計</h2>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <i className="fas fa-hiking"></i>
                            <div className="label">爬山次數</div>
                            <div className="value">{userRecords.length}</div>
                        </div>
                        <div className="stat-item">
                            <i className="fas fa-route"></i>
                            <div className="label">爬山總距離</div>
                            <div className="value">{
                                userRecords.reduce((total, record) => total + (record.length_km || 0), 0).toFixed(2)
                            } 公里</div>
                        </div>
                        <div className="stat-item">
                            <i className="fas fa-mountain"></i>
                            <div className="label">挑戰過的百岳</div>
                            <div className="value">{
                                new Set(userRecords.map(record => record.trail_id)).size
                            }/100</div>
                        </div>
                    </div>
                </div>

                <div className="profile-section">
                    <h2>過往登山紀錄</h2>
                    <ul className="profile-records">
                        {currentRecords.map(record => (
                            <li key={record.trail_id}>{record.date} {record.trail_name}</li>
                        ))}
                    </ul>
                    <div className="profile-pagination-buttons">
                        <button onClick={handlePrevPage} disabled={currentPage === 1}>上一頁</button>
                        <button onClick={handleNextPage} disabled={currentPage === totalPages}>下一頁</button>
                    </div>
                </div>

                <div className="profile-section">
                    <h2>登山建議報告</h2>
                    <p className="profile-report">
                        未來建議可考慮安排連續多日的縱走行程，例如合歡北峰－石門山－奇萊南華等，藉由多天路線累積經驗，培養在山區過夜的技能與適應能力。同時，若打算再次挑戰玉山或雪山主峰，建議嘗試不同季節登頂，如冬季的雪季路線，不僅視野壯闊，也能加強冰雪地形的技術應變能力，但必須搭配冰爪、冰斧等裝備與相關訓練。

                        其次，從紀錄來看，大部分行程集中在台灣百岳的熱門山域。未來可嘗試較少人踏足的中級山或郊山，像是大霸尖山周邊群峰或能高安東軍縱走，這些路線兼具挑戰與探索性，有助於拓展登山視野。此外，您可透過參加登山社團、山難防救課程或野外急救訓練，提升團隊合作與緊急應變能力，對於長期累積登山經驗非常關鍵。

                        最後，隨著登山頻率增加，建議定期檢視個人體能與裝備。保持有氧與重量訓練，以維持登山時的續航力與背負能力；裝備上則可逐步升級輕量化器材，減少長程行走的體力消耗。

                        綜合而言，您已具備紮實的單攻與中級山經驗，未來若能結合多日縱走、不同季節挑戰及技術訓練，不僅能提升登山實力，也能讓您的登山旅程更加多元與安全。
                    </p>
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
