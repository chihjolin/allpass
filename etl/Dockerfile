FROM python:3.12-slim

# 安裝必要套件
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安裝 ETL requirements
COPY etl/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製 ETL 程式碼
COPY etl/ /app/etl

# 複製 common
COPY common/ /app/common

# 安裝 common local package
RUN pip install -e .

# 預設執行 ETL 初始化腳本
CMD ["python", "etl/init/init_postgres.py"]
