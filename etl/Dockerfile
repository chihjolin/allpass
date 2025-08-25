FROM python:3.12-slim

# 安裝必要套件
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 複製 common 並安裝
COPY common/ /app/common
RUN pip install -e /app/common

# 複製 ETL 程式碼
COPY etl/ /app/etl

# 安裝 ETL requirements
WORKDIR /app/etl
RUN pip install --no-cache-dir -r requirements.txt

# 回到 /app 作為預設工作目錄
WORKDIR /app

# # 預設執行 ETL 初始化腳本
# CMD ["python", "etl/init/init_postgres.py"]

# 預設 CMD: 初始化後觸發 runner
#CMD ["python", "etl/runner_entry.py"]
CMD ["python", "-m", "etl.runner_entry"]
