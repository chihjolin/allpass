import logging
import os

import mlflow
import pandas as pd
import pytest
from dotenv import load_dotenv

# 開發測試用
load_dotenv(override=True)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MODEL_NAME = os.getenv("TIME_PREDICTION_MODEL_NAME")


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    logger.info(f"root ok: {response.json()["status"]}")


# def test_feature_list_consistency(model_features):
#     """
#     驗證載入後 pipeline 中 features 的順序與內容一致。
#     """
#     # 驗證 features 為 list
#     assert isinstance(model_features, list), "pipeline['features'] 應該是 list"

#     # 驗證 features 無重複
#     assert len(model_features) == len(set(model_features)), "features 有重複項"

#     # # 驗證 features 名稱內容一致
#     expected_features = [
#         "avg_temp",
#         "avg_rh",
#         "max_precip",
#         "distance",
#         "elevation_range",
#         "elevation_change",
#         "elevation_gain",
#         "elevation_loss",
#         "high_elevation",
#         "max_slope_percent",
#         "max_slope_degrees",
#         "slope_std_dev",
#         "slope_variance",
#         "max_slope_lat",
#         "max_slope_lon",
#         "slope_neg15",
#         "slope_neg15_neg10",
#         "slope_neg10_neg5",
#         "slope_neg5_neg1",
#         "slope_neg1_1",
#         "slope_1_5",
#         "slope_5_10",
#         "slope_10_15",
#         "slope_over15",
#         "accumulated_time_seconds",
#         "accumulated_distance",
#     ]
#     missing = set(expected_features) - set(model_features)
#     extra = set(model_features) - set(expected_features)
#     assert not missing, f"缺少特徵: {missing}"
#     assert not extra, f"多出未預期特徵: {extra}"

#     # 確認順序是否完全一致，也可以這樣：
#     assert model_features == expected_features, "特徵順序與訓練時不一致"


def test_model_predict_directly(loaded_model, model_features):
    """直接測試 MLflow 模型可預測"""
    sample = {f: 3.0 for f in model_features}
    df = pd.DataFrame([sample])

    result = loaded_model.predict(df)
    assert result is not None
    logger.info(f"Direct predict: {result}")


def test_predict_api_200(client, model_features):
    """正常預測案例"""
    features = {f: 1.0 for f in model_features}
    response = client.post("/predict/", json=features)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "predicted_spend_time_seconds" in data
    logger.info(f"200 OK: predicted {data['predicted_spend_time_seconds']:.2f} seconds")


def test_predict_api_422_invalid_input(client, model_features):
    """錯誤輸入（少欄位、型別錯誤）應回傳 422"""
    # 故意漏掉一個欄位、並將值改為字串
    bad_features = {f: 1.0 for f in model_features[:-1]}
    bad_features[model_features[0]] = "not_a_number"

    response = client.post("/predict/", json=bad_features)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    logger.info("422 correctly triggered for invalid input")


def test_predict_api_500_internal_error(
    monkeypatch, client, loaded_model, model_features
):
    """模擬模型預測異常應回傳 500"""

    good_features = {f: 1.0 for f in model_features}

    # 模擬模型.predict() 拋出例外
    def mock_predict_fail(_):
        raise RuntimeError("Mocked internal failure")

    monkeypatch.setattr(loaded_model, "predict", mock_predict_fail)

    # 替換 global MODEL
    from aiservices.time_prediction import predict as predict_module

    predict_module.MODEL = loaded_model

    response = client.post("/predict/", json=good_features)
    assert response.status_code == 500, f"Expected 500, got {response.status_code}"
    print("500 correctly triggered for internal model error")
