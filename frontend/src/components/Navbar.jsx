import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/Navbar.css';

export default function Navbar({ alwaysScrolled = false }) {
    const [isScrolled, setIsScrolled] = useState(alwaysScrolled);
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

    const handleLoginClick = () => {
        navigate('/login');
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
                        <li><Link to="/about">關於我們</Link></li>
                    </ul>
                </div>
                <div className="navbar-right">
                    <button className="navbar-login-button" onClick={handleLoginClick}>
                        <img src="/icons/login.avif" alt="Login" className="login-icon" />
                    </button>
                </div>
            </div>
        </nav>
    );
}
