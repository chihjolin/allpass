import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/Navbar.css';

export default function Navbar({ alwaysScrolled = false }) {
    const [isScrolled, setIsScrolled] = useState(alwaysScrolled);
    const [isLoggedIn, setIsLoggedIn] = useState(false); // 用於追蹤登入狀態
    const navigate = useNavigate();

    useEffect(() => {
        if (alwaysScrolled) return;

        const handleScroll = () => {
            if (window.scrollY > 630) {
                setIsScrolled(true);
            } else {
                setIsScrolled(false);
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [alwaysScrolled]);

    // 檢查登入狀態
    useEffect(() => {
        const userId = localStorage.getItem('user_id');
        setIsLoggedIn(!!userId); // 如果 user_id 存在，表示已登入
    }, []);

    const handleLoginClick = () => {
        navigate('/login');
    };

    const handleLogoutClick = () => {
        // 清除 localStorage 中的用戶資訊
        localStorage.removeItem('user_id');
        localStorage.removeItem('username');

        // 更新登入狀態
        setIsLoggedIn(false);

        alert('已成功登出！');
        navigate('/'); // 登出後跳轉到首頁
    };

    return (
        <nav className={`navbar ${isScrolled ? 'scrolled' : ''}`}>
            <div className="navbar-container">
                <div className="navbar-left">
                    <div className="navbar-logo">
                        <Link to="/">All爬ss</Link>
                    </div>
                    <ul className="navbar-links">
                        <li><Link to="/">首頁</Link></li>
                        <li><Link to="/profile">個人紀錄</Link></li>
                    </ul>
                </div>
                <div className="navbar-right">
                    {isLoggedIn ? (
                        <button className="navbar-login-button" onClick={handleLogoutClick}>
                            <img src="/icons/login.avif" alt="Logout" className="login-icon" />
                        </button>
                    ) : (
                        <button className="navbar-login-button" onClick={handleLoginClick}>
                            <img src="/icons/login.avif" alt="Login" className="login-icon" />
                        </button>
                    )}
                </div>
            </div>
        </nav>
    );
}
