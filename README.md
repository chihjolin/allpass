## 專案結構  
```
frontend/
├── node_modules/               # 第三方依賴模組
├── public/                     # 公開資源 (如 favicon、manifest 等)
├── src/                       
│   ├── components/             # React 組件
│   ├── pages/                  # 不同頁面元件（搭配路由）
│   ├── App.jsx                 # React 主組件
│   ├── main.jsx                # 應用程式的進入點
│   └── styles.css              
├── Dockerfile                  
├── index.html                  # HTML 模板入口
├── nginx.conf                  # Nginx 設定檔
├── package-lock.json           # npm 鎖定依賴版本
├── package.json                # 專案描述與依賴清單
└── vite.config.js              # Vite 設定


```
## 使用說明    
### 進入前端開發伺服器
- 下載node js  
```
cd frontend
npm install
npm run dev
```
localhost:5173
### 或者用Docker
用docker的話每次React有修改都要重built映像檔喔