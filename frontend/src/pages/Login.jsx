import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/Login.css';

// user: user1@example.com
// password: password123

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (event) => {
        event.preventDefault();
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                }),
            });

            const data = await response.json();
            if (data.message === "Login successful") {
                // 登入成功，將 user_id 和 username 存儲到 localStorage
                localStorage.setItem('user_id', data.data.user_id);
                localStorage.setItem('username', data.data.username);

                navigate('/'); // 登入成功後導回首頁
            } else {
                setErrorMessage(data.message || '登入失敗，請檢查您的帳號和密碼。');
            }
        } catch (error) {
            navigate('/');
            // setErrorMessage('伺服器錯誤，請稍後再試。');
        }
    };

    return (
        <div className="login-page-container">
            <div className="login-image-container">
                <img src="img/login_mountain.avif" alt="Login Image" />
            </div>
            <div className="login-form-container">
                <h1>WELCOME</h1>
                <p>準備開啟你的爬山之路吧少年!</p>
                <form onSubmit={handleLogin}>
                    <label htmlFor="email">User</label>
                    <input
                        type="email"
                        id="email"
                        placeholder="aipe01@gmail.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />

                    <label htmlFor="password">Password</label>
                    <input
                        type="password"
                        id="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />

                    {errorMessage && <p className="error-message">{errorMessage}</p>}

                    <button type="submit" className="login-button-container">Login</button>
                </form>
            </div>
        </div>
    );
}
