# aiservices/time_prediction/predict.py

import glob
import os
from contextlib import asynccontextmanager
from typing import List, Optional

import joblib
import mlflow
import numpy as np
import pandas as pd

# 載入環境變數(開發測試用)
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from mlflow.tracking import MlflowClient
from pydantic import BaseModel

load_dotenv(override=True)

# ------------ MLflow / MinIO 設定 ------------
MLFLOW_HOST = os.getenv("MLFLOW_HOST", "mlflow")
MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5000")
MLFLOW_URI = f"http://{MLFLOW_HOST}:{MLFLOW_PORT}"
mlflow.set_tracking_uri(MLFLOW_URI)

# Minio artifact store
MINIO_HOST = os.getenv("MINIO_HOST")
MINIO_PORT = os.getenv("MINIO_PORT")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
# MINIO_BUCKET_NAME=os.getenv("MINIO_BUCKET_NAME")

# 設定 MLflow 要存取 S3 (MinIO) 的環境變數（必須在載入 model 前設定)
AWS_ACCESS_KEY_ID = MINIO_ROOT_USER
AWS_SECRET_ACCESS_KEY = MINIO_ROOT_PASSWORD
MLFLOW_S3_ENDPOINT_URL = f"http://{MINIO_HOST}:{MINIO_PORT}"

# 設定環境變數: MLflow 讀 artifact store 設定會讀環境變數
os.environ["AWS_ACCESS_KEY_ID"] = MINIO_ROOT_USER
os.environ["AWS_SECRET_ACCESS_KEY"] = MINIO_ROOT_PASSWORD
os.environ["MLFLOW_S3_ENDPOINT_URL"] = MLFLOW_S3_ENDPOINT_URL
# os.environ["MLFLOW_ARTIFACT_URI"] = f"s3://{MINIO_BUCKET_NAME}"

print("MLflow tracking URI:", mlflow.get_tracking_uri())
print("MLflow S3 Endpoint:", os.environ.get("MLFLOW_S3_ENDPOINT_URL"))
print("AWS Access Key:", os.environ.get("AWS_ACCESS_KEY_ID"))
print("AWS Secret Key:", os.environ.get("AWS_SECRET_ACCESS_KEY"))

client = MlflowClient()
model_name = "time_prediction_model"

# Global cached model and version
MODEL = None
MODEL_VERSION = None


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


# --------------- Helper: 載入 Model ---------------
def load_model_from_registry(
    model_name: str, stage: str = "Production", wait: bool = False
):
    """
    從 MLflow Registry 載入 models:/{name}/{stage}。
    Args:
        model_name (str): 模型註冊名稱
        stage(str): Staging/Production/Archived
        wait(bool): 是否等待
    Returns:
       回傳 (model, version)；若找不到回傳 (None, None)。
    """
    try:
        # 查詢 stage 階段的版本
        versions = client.get_latest_versions(name=model_name, stages=[stage])
        if not versions:
            print(f"[load_model] no version in stage {stage} for model {model_name}")
            return None, None

        version_info = versions[0]
        version_number = version_info.version
        model_uri = f"models:/{model_name}/{stage}"
        print(f"[load_model] loading {model_uri} (version {version_number}) ...")
        # 載入模型
        model = mlflow.pyfunc.load_model(model_uri)
        print(f"[load_model] loaded model stage{stage}, version {version_number}")
        return model, version_number

    except Exception as e:
        print(f"[load_model] failed to load model: {model_name}; stage {stage}: {e}")
        return None, None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用啟動時嘗試載入 Production 模型（快取到全域 MODEL）。
    """
    global MODEL, MODEL_VERSION
    print("[startup] trying to load model from registry ...")
    MODEL, MODEL_VERSION = load_model_from_registry(model_name, stage="Production")
    if MODEL is None:
        print(
            "[startup] no production model loaded. /predict will return 503 until model is loaded."
        )
    yield
    # 釋放資源
    print("[shutdown] application is shutting down...")


# --- FastAPI 應用程式實例 ---
app = FastAPI(title="Time Prediction API", version="1.0", lifespan=lifespan)


# --- API 端點 (Endpoint) ---
@app.get("/")
def read_root():
    return {
        "status": "Time Prediction API is running.",
        "mlflow_uri": mlflow.get_tracking_uri(),
        "model_loaded": MODEL_VERSION,
    }


@app.post("/reload-model/")
def reload_model(stage: Optional[str] = "Production"):
    """
    HTTP endpoint to force reload the model from registry (useful after model version promotion).
    """
    global MODEL, MODEL_VERSION
    model, ver = load_model_from_registry(model_name, stage=stage)
    if model is None:
        raise HTTPException(
            status_code=404, detail=f"No model found for {model_name} stage {stage}"
        )
    MODEL, MODEL_VERSION = model, ver
    return {
        "status": "reloaded",
        "model": model_name,
        "version": MODEL_VERSION,
        "stage": stage,
    }


@app.post("/predict/")
def predict(features: Features):
    """
    使用 cached MODEL 進行預測。
    """
    global MODEL
    if MODEL is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Call /reload-model or wait for startup load.",
        )

    try:
        # Pydantic -> DataFrame
        input_df = pd.DataFrame([features.model_dump()])

        # 直接使用 mlflow pyfunc model 的 predict
        preds = MODEL.predict(input_df)  # 可能是 numpy array 或 list

        arr = np.array(preds).ravel()
        # 支援多筆或單筆輸入。這裡假設單筆輸入，回傳第一個預測值。
        final_pred = float(arr[0]) if arr.size > 0 else None

        return {"predicted_spend_time_seconds": final_pred, "raw": arr.tolist()}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
