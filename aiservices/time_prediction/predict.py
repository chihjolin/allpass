# aiservices/time_prediction/predict.py

import glob
import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional

import joblib
import mlflow
import numpy as np
import pandas as pd

# # 載入環境變數(開發測試用)
# from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from mlflow.tracking import MlflowClient
from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# load_dotenv(override=True)


def init_mlflow():
    # ------------ MLflow / MinIO 設定 ------------
    MLFLOW_HOST = os.getenv("MLFLOW_HOST", "mlflow")
    MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5000")
    MLFLOW_URI = f"http://{MLFLOW_HOST}:{MLFLOW_PORT}"
    mlflow.set_tracking_uri(MLFLOW_URI)
    logger.info(f"MLflow URI: {mlflow.get_tracking_uri()}")

    # Minio artifact store
    MINIO_HOST = os.getenv("MINIO_HOST")
    MINIO_PORT = os.getenv("MINIO_PORT")
    MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
    MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
    # MINIO_BUCKET_NAME=os.getenv("MINIO_BUCKET_NAME")

    # 設定 MLflow 要存取 S3 (MinIO) 的環境變數（必須在載入 model 前設定)
    if MINIO_HOST and MINIO_PORT and MINIO_ROOT_USER and MINIO_ROOT_PASSWORD:
        os.environ["AWS_ACCESS_KEY_ID"] = MINIO_ROOT_USER
        os.environ["AWS_SECRET_ACCESS_KEY"] = MINIO_ROOT_PASSWORD
        os.environ["MLFLOW_S3_ENDPOINT_URL"] = f"http://{MINIO_HOST}:{MINIO_PORT}"
        logger.info(f"AWS Access Key: {os.environ.get('AWS_ACCESS_KEY_ID')}")
        logger.info(f"AWS Secret Key: {os.environ.get('AWS_SECRET_ACCESS_KEY')}")
        logger.info(f"MLflow S3 Endpoint: {os.environ.get('MLFLOW_S3_ENDPOINT_URL')}")
    else:
        logger.warning(
            "MinIO environment variables not fully set; MLflow may not access artifacts"
        )

    return MlflowClient()


client = None
model_name = os.getenv("TIME_PREDICTION_MODEL_NAME")
logger.info(f"model_name: {model_name}")

# Global cached model and version
MODEL = None
MODEL_VERSION = None
Features = None


# --------------- Helper: 載入 Model ---------------
def load_model_from_registry(model_name: str, stage: str = "Production"):
    """
    從 MLflow Registry 載入 models:/{name}/{stage}。
    Args:
        model_name (str): 模型註冊名稱
        stage(str): Staging/Production/Archived
    Returns:
       回傳 (model, version)；若找不到回傳 (None, None)。
    """
    global client
    if client is None:
        client = init_mlflow()
    try:
        # 查詢 stage 階段的版本
        versions = client.get_latest_versions(name=model_name, stages=[stage])
        if not versions:
            logger.warning(f"No version found for {model_name}:{stage}")
            # print(f"[load_model] no version in stage {stage} for model {model_name}")
            return None, None

        version_info = versions[0]
        version_number = version_info.version
        model_uri = f"models:/{model_name}/{stage}"
        logger.info(f"loading {model_uri} (version {version_number}) ...")
        # print(f"[load_model] loading {model_uri} (version {version_number}) ...")
        # 載入模型
        model = mlflow.pyfunc.load_model(model_uri)
        logger.info(
            f"Loaded model {model_name} (version: {version_number}) from stage {stage}"
        )
        # print(f"Loaded model {model_name} (version: {version_number}) from stage {stage}")
        return model, version_number

    except Exception as e:
        logger.error(f"Load model failed: {model_name}; stage {stage}: {e}")
        # print(f"[load_model] failed to load model: {model_name}; stage {stage}: {e}")
        return None, None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用啟動時嘗試載入 Production 模型（快取到全域 MODEL）。
    """
    # 在模組層定義了 MODEL = None；要在函式內讀/寫需加 global
    global MODEL, MODEL_VERSION, Features
    logger.info("[startup] Starting lifespan: loading production model on startup...")
    MODEL, MODEL_VERSION = load_model_from_registry(model_name, stage="Production")
    if MODEL is None:
        raise HTTPException(
            status_code=404,
            detail=f"[startup] no production model loaded. /predict will return 503 until model is loaded.",
        )
    # 根據模型內 pipeline["features"] 動態建立 Pydantic schema
    py_model = getattr(MODEL._model_impl, "python_model", None)
    if py_model is None or not hasattr(py_model, "pipeline"):
        raise HTTPException(
            status_code=500, detail="Loaded model has no pipeline attribute."
        )
    feature_list = py_model.pipeline["features"]
    # feature_list = MODEL.pipeline["features"]
    Features = create_model(
        "Features",
        **{f: (float, ...) for f in feature_list},
    )
    logger.info(f"Dynamically created Features model with {len(feature_list)} fields")
    logger.info(f"Model features: {feature_list}")
    yield
    # 釋放資源
    logger.info("Done lifespan: App shutdown complete.")


# --- FastAPI 應用程式實例 ---
app = FastAPI(title="Time Prediction API", version="1.0", lifespan=lifespan)


# --- API 端點 (Endpoint) ---
@app.get("/")
def read_root():
    return {
        "status": "Time Prediction API is running.",
        "mlflow_uri": mlflow.get_tracking_uri(),
        "model_loaded_version": MODEL_VERSION,
        "num_features": (
            len(MODEL._model_impl.python_model.pipeline["features"]) if MODEL else None
        ),
    }


@app.post("/reload-model/")
def reload_model(stage: Optional[str] = "Production"):
    """
    HTTP endpoint to force reload the model from registry (useful after model version promotion).
    """
    global MODEL, MODEL_VERSION, Features
    MODEL, MODEL_VERSION = load_model_from_registry(model_name, stage=stage)
    if MODEL is None:
        raise HTTPException(
            status_code=404, detail=f"No model found for {model_name} stage {stage}"
        )

    py_model = getattr(MODEL._model_impl, "python_model", None)
    if py_model is None or not hasattr(py_model, "pipeline"):
        raise HTTPException(
            status_code=500, detail="Loaded model has no pipeline attribute."
        )
    feature_list = py_model.pipeline["features"]
    # feature_list = MODEL.pipeline["features"]
    Features = create_model("Features", **{f: (float, ...) for f in feature_list})
    return {
        "status": "reloaded",
        "model": model_name,
        "version": MODEL_VERSION,
        "stage": stage,
    }


@app.post("/predict/")
def predict(features: dict, simulate_error: bool = False):
    """
    使用 cached MODEL 進行預測。
    """
    global MODEL, Features
    # logger.info(f"DEBUG: MODEL is {type(MODEL)}, Features is {type(Features)}")
    if MODEL is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Call /reload-model or wait for startup load.",
        )
    if Features is None:
        raise HTTPException(
            status_code=503,
            detail="Retrieve Features failed",
        )

    try:
        if simulate_error:
            raise RuntimeError("Simulated model error")
        # 使用動態 Pydantic 驗證輸入(驗證、型別轉換、欄位順序、未來擴充)
        validated = Features(**features)

        # Pydantic -> model_dump(): Python dict -> DataFrame
        input_df = pd.DataFrame([validated.model_dump()])

        # 直接使用 mlflow pyfunc model 的 predict
        preds = MODEL.predict(input_df)  # 常見輸出可能是 numpy array 或 list

        # 將任何 shape 的輸出攤平成 1-d array
        arr = np.array(preds).ravel()

        # 支援多筆或單筆輸入。這裡假設單筆輸入，回傳第一個預測值。
        final_pred = float(arr[0]) if arr.size > 0 else None

        return {"predicted_spend_time_seconds": final_pred, "raw": arr.tolist()}
    except ValueError as e:
        # FastAPI 會把 request body 的 JSON parse 成 Features（Pydantic model）並做型別驗證（若失敗回 422）
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Internal model error")
