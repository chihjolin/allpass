# backend/Dockerfile
FROM python:3.12-slim

# 安裝必要套件（與 ETL 保持一致）
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 複製 common 並安裝 (editable mode 方便開發)
COPY common/ /app/common
RUN pip install -e /app/common

# 複製 backend 程式碼
COPY backend/ /app/backend

# 安裝 backend requirements
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# 預設工作目錄
WORKDIR /app

# 啟動 backend (Flask API)
CMD ["python", "backend/app.py"]
#CMD ["python", "-m", "backend.app"]
