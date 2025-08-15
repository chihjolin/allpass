import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
    const [isOpen, setIsOpen] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            if (window.scrollY > 630) { // 假設 header 高度為 100px
                setIsScrolled(true);
            } else {
                setIsScrolled(false);
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const toggleMenu = () => {
        setIsOpen(!isOpen);
    };

    return (
        <nav className={`navbar ${isScrolled ? 'scrolled' : ''}`}>
            <div className="navbar-container">
                <div className="navbar-logo">
                    <Link to="/">All爬ss</Link>
                </div>
                <button className="menu-toggle" onClick={toggleMenu}>
                    <span className="menu-icon">{isOpen ? '✖' : '☰'}</span>
                </button>
                <ul className={`navbar-links ${isOpen ? 'open' : ''}`}>
                    <li><Link to="/">首頁</Link></li>
                    <li><Link to="/plan/1">路線規劃</Link></li>
                    <li><Link to="/about">關於我們</Link></li>
                </ul>
            </div>
        </nav>
    );
}
