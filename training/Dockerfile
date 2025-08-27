# training/Dockerfile
FROM python:3.12-slim

# 安裝 XGBoost 可能需要的系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 複製 common 並安裝 (editable mode 方便開發)
COPY common/ /app/common
RUN pip install -e /app/common

# 複製 training 程式碼
COPY training/ /app/training

# 安裝 training requirements
WORKDIR /app/training
RUN pip install --no-cache-dir -r requirements.txt

# 預設工作目錄
WORKDIR /app

# 啟動 training
CMD ["python", "training/train.py"]
