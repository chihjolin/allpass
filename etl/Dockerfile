# 選擇 Python 基礎映像
FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製整個專案到容器
COPY . .

# 設定 PYTHONPATH 讓 utils 可以被找到
ENV PYTHONPATH=/app

# 預設執行指令 (可改成你的 ETL 主程式)
CMD ["python", "-m", "init.init_postgres"]