import logging
import os

import mlflow
import pandas as pd
import pytest
import requests as rq
from dotenv import load_dotenv

# 開發測試用
load_dotenv(override=True)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


model_name = os.getenv("TIME_PREDICTION_MODEL_NAME")


def test_root(api_url):
    # response = client.get("/")
    response = rq.get(f"{api_url}/")
    assert response.status_code == 200
    assert "status" in response.json()
    logger.info(f"root ok: {response.json()["status"]}")


def test_model_predict_directly(loaded_model, model_features):
    """直接測試 MLflow 模型可預測"""
    sample = {f: 3.0 for f in model_features}
    df = pd.DataFrame([sample])

    result = loaded_model.predict(df)
    assert result is not None
    logger.info(f"Direct predict: {result}")


def test_predict_api_200(api_url, model_features):
    """正常預測案例"""
    features = {f: 1.0 for f in model_features}
    response = rq.post(f"{api_url}/predict/", json=features)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "predicted_spend_time_seconds" in data
    logger.info(f"200 OK: predicted {data['predicted_spend_time_seconds']:.2f} seconds")


def test_predict_api_422_invalid_input(api_url, model_features):
    """錯誤輸入（少欄位、型別錯誤）應回傳 422"""
    # 故意漏掉一個欄位、並將值改為字串
    bad_features = {f: 1.0 for f in model_features[:-1]}
    bad_features[model_features[0]] = "not_a_number"

    response = rq.post(f"{api_url}/predict/", json=bad_features)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    logger.info("422 correctly triggered for invalid input")


def test_predict_api_500_internal_error(
    monkeypatch, api_url, loaded_model, model_features
):
    """模擬模型預測異常應回傳 500"""

    good_features = {f: 1.0 for f in model_features}

    # # 模擬模型.predict() 拋出例外
    # def mock_predict_fail(_):
    #     raise RuntimeError("Mocked internal failure")

    # monkeypatch.setattr(loaded_model, "predict", mock_predict_fail)

    # # 替換 global MODEL
    # from aiservices.time_prediction import predict as predict_module

    # predict_module.MODEL = loaded_model

    response = rq.post(f"{api_url}/predict/?simulate_error=true", json=good_features)
    assert response.status_code == 500, f"Expected 500, got {response.status_code}"
    logger.info("500 correctly triggered for internal model error")
