import logging
import os

import mlflow
import pandas as pd
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from aiservices.time_prediction.predict import (
    MODEL,
    Features,
    app,
    lifespan,
    load_model_from_registry,
)

# 開發測試用
load_dotenv(override=True)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MODEL_NAME = os.getenv("TIME_PREDICTION_MODEL_NAME")


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


@pytest.fixture(scope="session")
def client():
    """FastAPI 測試用 client"""
    return TestClient(app)


# @pytest.fixture(scope="module")
# def loaded_model():
#     model_uri = f"models:/{MODEL_NAME}/Production"
#     model = mlflow.pyfunc.load_model(model_uri)
#     return model._model_impl.python_model  # 直接回傳 TimePredictionModel 實例


@pytest.fixture(scope="session")
def loaded_model():
    """從 MLflow Registry 載入真實模型"""
    model_name = os.getenv("TIME_PREDICTION_MODEL_NAME")
    model, version = load_model_from_registry(model_name, stage="Production")
    assert model is not None, f"Model {model_name} not found in Production stage!"
    print(f"Loaded {model_name} (version {version})")
    return model


def test_feature_list_consistency(loaded_model):
    """
    驗證載入後 pipeline 中 features 的順序與內容一致。
    """
    pipeline_features = loaded_model._model_impl.python_model.pipeline["features"]

    # 驗證 features 為 list
    assert isinstance(pipeline_features, list), "pipeline['features'] 應該是 list"

    # 驗證 features 無重複
    assert len(pipeline_features) == len(set(pipeline_features)), "features 有重複項"

    # # 驗證 features 名稱內容一致
    # expected_features = ["distance_km", "elevation_gain_m", "descent_m", "avg_slope"]
    # missing = set(expected_features) - set(pipeline_features)
    # extra = set(pipeline_features) - set(expected_features)
    # assert not missing, f"缺少特徵: {missing}"
    # assert not extra, f"多出未預期特徵: {extra}"

    # # 如果你想確認順序完全一致，也可以這樣：
    # assert pipeline_features == expected_features, "特徵順序與訓練時不一致"


def test_model_predict_directly(loaded_model):
    """直接測試 MLflow 模型可預測"""
    feature_list = loaded_model._model_impl.python_model.pipeline["features"]
    sample = {f: 1.0 for f in feature_list}
    df = pd.DataFrame([sample])

    result = loaded_model.predict(df)
    assert result is not None
    print("Direct predict:", result)


def test_predict_api_200(client, loaded_model):
    """正常預測案例"""
    feature_list = loaded_model._model_impl.python_model.pipeline["features"]
    features = {f: 1.0 for f in feature_list}

    response = client.post("/predict/", json={"features": features})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "predicted_spend_time_seconds" in data
    print(f"200 OK: predicted {data['predicted_spend_time_seconds']:.2f} seconds")


def test_predict_api_422_invalid_input(client, loaded_model):
    """錯誤輸入（少欄位、型別錯誤）應回傳 422"""
    feature_list = loaded_model._model_impl.python_model.pipeline["features"]

    # 故意漏掉一個欄位、並將值改為字串
    bad_features = {f: 1.0 for f in feature_list[:-1]}
    bad_features[feature_list[0]] = "not_a_number"

    response = client.post("/predict/", json={"features": bad_features})
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    print("422 correctly triggered for invalid input")


def test_predict_api_500_internal_error(monkeypatch, client, loaded_model):
    """模擬模型預測異常應回傳 500"""

    feature_list = loaded_model._model_impl.python_model.pipeline["features"]
    good_features = {f: 1.0 for f in feature_list}

    # 模擬模型.predict() 拋出例外
    def mock_predict_fail(_):
        raise RuntimeError("Mocked internal failure")

    monkeypatch.setattr(loaded_model, "predict", mock_predict_fail)

    # 替換 global MODEL
    from aiservices.time_prediction import predict as predict_module

    predict_module.MODEL = loaded_model

    response = client.post("/predict/", json={"features": good_features})
    assert response.status_code == 500, f"Expected 500, got {response.status_code}"
    print("500 correctly triggered for internal model error")
