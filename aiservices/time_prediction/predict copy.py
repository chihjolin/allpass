# aiservices/time_prediction/predict.py

import glob
import os
from typing import List

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow
from mlflow.tracking import MlflowClient
from dotenv import load_dotenv



# 載入環境變數(開發測試用)
load_dotenv(override=True)


# -----------------------------
# MLflow, MinIO 設定
# -----------------------------
MLFLOW_HOST = os.getenv("MLFLOW_HOST", "localhost")
MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5001")
MLFLOW_URI = f"http://{MLFLOW_HOST}:{MLFLOW_PORT}"
mlflow.set_tracking_uri(MLFLOW_URI)

MINIO_HOST=os.getenv("MINIO_HOST")
MINIO_PORT=os.getenv("MINIO_PORT")
MINIO_ROOT_USER=os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD=os.getenv("MINIO_ROOT_PASSWORD")

AWS_ACCESS_KEY_ID = MINIO_ROOT_USER
AWS_SECRET_ACCESS_KEY = MINIO_ROOT_PASSWORD
MLFLOW_S3_ENDPOINT_URL= f"http://{MINIO_HOST}:{MINIO_PORT}"

#設定環境變數: MLflow 讀 artifact store 設定會讀環境變數
os.environ["AWS_ACCESS_KEY_ID"] = MINIO_ROOT_USER
os.environ["AWS_SECRET_ACCESS_KEY"] = MINIO_ROOT_PASSWORD
os.environ["MLFLOW_S3_ENDPOINT_URL"] = MLFLOW_S3_ENDPOINT_URL

client = MlflowClient()
model_name = "time_prediction_model"


# --- Pydantic 模型定義 API 的輸入格式 ---
# 這裡的欄位「必須」跟你訓練時的特徵完全對應
class Features(BaseModel):
    avg_temp: float
    avg_rh: float
    max_precip: float
    distance: float
    elevation_range: float
    elevation_change: float
    elevation_gain: float
    elevation_loss: float
    high_elevation: float
    max_slope_percent: float
    max_slope_degrees: float
    slope_std_dev: float
    slope_variance: float
    max_slope_lat: float
    max_slope_lon: float
    slope_neg15: float
    slope_neg15_neg10: float
    slope_neg10_neg5: float
    slope_neg5_neg1: float
    slope_neg1_1: float
    slope_1_5: float
    slope_5_10: float
    slope_10_15: float
    slope_over15: float
    accumulated_time_seconds: float
    accumulated_distance: float


# --- FastAPI 應用程式實例 ---
app = FastAPI(title="Time Prediction API", version="1.0")

# --- 模型載入 ---
# 使用全域變數來存放載入的模型，避免每次請求都重新載入，提升效能
PIPELINE = None
MODEL_PATH = "/app/models"  # 容器內的路徑


def find_latest_model_path(path: str) -> str:
    """在指定路徑中尋找最新的 .pkl 模型檔案"""
    # 列出所有 .pkl 檔案
    list_of_files = glob.glob(os.path.join(path, "time_prediction_*.pkl"))
    if not list_of_files:
        return None
    # 根據檔名 (隱含了時間戳) 找到最新的檔案
    latest_file = max(list_of_files, key=os.path.basename)
    return latest_file

def load_production_model(model_name:str):    
    """
    從 MLflow Model Registry 載入標註為 Production 的模型，並印出版本號。
    Args:
        model_name (str): 模型註冊名稱  
    Returns:
        model: 可用於預測的 MLflow PyFunc 模型
    """
    try:
        # 查詢 Production 階段的版本
        versions = client.get_latest_versions(name=model_name, stages=["Production"])
        if not versions:
            print(f"模型 '{model_name}' 沒有標註為 Production 的版本")
            return None

        version_info = versions[0]
        version_number = version_info.version
        print(f"模型 '{model_name}' 的 Production 版本為：{version_number}")

        # 載入模型
        model = mlflow.pyfunc.load_model(f"models:/{model_name}/Production")
        print(f"成功載入模型 '{model_name}' 的 Production 版本")
        return model

    
    except Exception as e:
        print(f"載入模型失敗: {e}")
        return None



@app.on_event("startup")
def load_model():
    """在應用程式啟動時執行的函式"""
    global PIPELINE
    latest_model_path = find_latest_model_path(MODEL_PATH)

    if latest_model_path:
        print(f"Loading model from: {latest_model_path}")
        PIPELINE = joblib.load(latest_model_path)
    else:
        print(f"No model found in {MODEL_PATH}")
        # 在這裡可以決定是否要讓應用程式因找不到模型而啟動失敗
        PIPELINE = None


# --- API 端點 (Endpoint) ---
@app.get("/")
def read_root():
    return {"status": "Time Prediction API is running."}


@app.post("/predict/")
def predict(features: Features):
    """接收特徵並回傳預測結果"""
    if PIPELINE is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    try:
        # 將 Pydantic 模型轉換為 DataFrame
        # input_df = pd.DataFrame([features.dict()])
        input_df = pd.DataFrame([features.model_dump()])

        # 確保 DataFrame 的欄位順序與訓練時一致
        # PIPELINE['features'] 是我們在 train.py 中刻意存下來的
        ordered_df = input_df[PIPELINE["features"]]

        # 使用儲存的 scaler 進行特徵縮放
        scaled_features = PIPELINE["scaler"].transform(ordered_df)

        # 使用集成模型進行預測
        predictions = [model.predict(scaled_features) for model in PIPELINE["models"]]

        # 計算平均預測值
        final_prediction = np.mean(predictions)

        return {"predicted_spend_time_seconds": float(final_prediction)}

    except Exception as e:
        # 捕捉任何可能的錯誤
        raise HTTPException(status_code=400, detail=str(e))
