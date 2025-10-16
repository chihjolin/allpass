import logging
import os

import mlflow
import pandas as pd
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from aiservices.time_prediction.predict import app, load_model_from_registry

# 開發測試用
load_dotenv(override=True)
time_prediction_host = os.getenv("TIME_PREDICTION_HOST")
time_prediction_port = os.getenv("TIME_PREDICTION_PORT")
BASE_URL = f"http://{time_prediction_host}:{time_prediction_port}"
model_name = os.getenv("TIME_PREDICTION_MODEL_NAME")

# @pytest.fixture(scope="session", autouse=True)
# def setup_env():
#     """讀取 .env 或設置必要環境變數"""
#     os.environ.setdefault("MLFLOW_HOST", "mlflow")
#     os.environ.setdefault("MLFLOW_PORT", "5000")
#     os.environ.setdefault("MINIO_HOST", "minio")
#     os.environ.setdefault("MINIO_PORT", "9000")
#     os.environ.setdefault("MINIO_ROOT_USER", "minio_rootuser")
#     os.environ.setdefault("MINIO_ROOT_PASSWORD", "minio_password")
#     os.environ.setdefault("MODEL_NAME", "time_prediction_model")
#     yield


# @pytest.fixture(scope="session")
# def client():
#     """確保 lifespan (startup/shutdown) 有正確執行"""
#     with TestClient(app) as c:
#         yield c


@pytest.fixture(scope="session")
def api_url():
    """提供 container 的 base URL"""
    return BASE_URL


@pytest.fixture(scope="session")
def loaded_model():
    """從 MLflow Registry 載入真實模型"""
    model_name = os.getenv("TIME_PREDICTION_MODEL_NAME")
    model, version = load_model_from_registry(model_name, stage="Production")
    assert model is not None, f"Model {model_name} not found in Production stage!"
    print(f"Loaded {model_name} (version {version})")
    return model


@pytest.fixture(scope="session")
def model_features(loaded_model):
    """從已載入的模型中提取特徵列表"""
    try:
        features = loaded_model._model_impl.python_model.pipeline["features"]
        return features
    except (AttributeError, KeyError):
        pytest.fail("無法從模型中提取 'features'。請檢查模型的內部結構。")
