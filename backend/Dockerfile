#Dockerfile:backend
FROM python:3.12-slim
# 安裝 curl，並清理 apt 快取，減少映像大小
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . . 
CMD ["python", "app.py"]