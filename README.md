## 專案結構  
```
allpass
├── backend
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   ├── resources
│   │   ├── gpxanalyzer.py
│   │   ├── hello.py
│   │   ├── map.py
│   │   ├── tiles.py
│   │   ├── trails.py
│   │   └── weather.py
│   └── utils
│       └── sql.py
├── db
│   ├── Dockerfile
│   └── database.json
├── docker-compose.yml
├── frontend
│   ├── Dockerfile
│   ├── data
│   │   └── map_cood.json
│   └── static
│       ├── icons
│       ├── index.html
│       ├── libs
│       │   └── leaflet
│       ├── manifest.json
│       ├── plan.html
│       ├── script.js
│       ├── styles.css
│       ├── sw.js
│
└── README.md
```
## 使用說明    
### 本地安裝nginx+ 修改設定檔-nginx.conf(範例)  
```
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /pathtoproject/allpass/frontend/static;
    index index.html;

    server_name _;
    
    location /api/ {
	    proxy_pass http://localhost:5000/api/;
	    proxy_set_header Host $host;
	    proxy_set_header X-Real-IP $remote_addr;
	    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	    proxy_set_header X-Forwarded-Proto $scheme;
	    }

    location / {
        try_files $uri /index.html;
        #try_files $uri $uri/ =404;
    }
    }
```
### 專案環境變數  
### /backend/.env(範例)  
```
#中央氣象局API
CWA_API_KEY=123
CWA_API_BASE=base_url
WEATHER_ENDPOINT=endpoint
```