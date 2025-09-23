# aiservices/time_prediction/predict.py

import glob
import os
from typing import List

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


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
