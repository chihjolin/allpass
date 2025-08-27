# aiservices/time_prediction/Dockerfile

FROM python:3.12-slim

WORKDIR /app

# 複製 common 並安裝 (editable mode 方便開發)
COPY common/ /app/common
RUN pip install -e /app/common

# 複製 aiservices/time_prediction 程式碼
COPY aiservices/time_prediction/ /app/time_prediction

# 安裝 aiservices/time_prediction requirements
WORKDIR /app/time_prediction
RUN pip install --no-cache-dir -r requirements.txt

# 開放 8000 port，讓外部可以連線
EXPOSE 8000

# 容器啟動時執行的命令
# uvicorn: 伺服器
# predict: Python 檔名 (predict.py)
# app: FastAPI 實例的變數名稱 (app = FastAPI())
# --host 0.0.0.0: 監聽所有網路介面，讓容器外部可以存取
# --port 8000: 在容器內使用的 port
CMD ["uvicorn", "predict:app", "--host", "0.0.0.0", "--port", "8000"]