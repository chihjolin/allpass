import json
import os

import requests as req
from flask import request
from flask_restful import Resource, reqparse
from pydantic import BaseModel

from common.utils.dbcon import engine
from common.utils.redis_client import get_redis_client

# 取得使用者行進當下時間(推論特徵), 傳給模型並返回模型預測結果


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


class Predictions(Resource):
    def post(self):
        """
        接收使用者行進當下時間,封裝特徵,傳給模型服務並接收模型預測結果(time_spend_seconds)
        1. 取得trail_id, poi_id, poi_order
        2. 寫進postgres:poi_visit_records
        3. 目前進度:取得還剩下幾個通訊點 -> 回傳幾段預測時間(秒)
        4. trail_id + (poi_c_id + poi_n_id -> segment_order)查該路段地形特徵(Redis)
        5. accumulated_time_seconds -> 查詢他本次爬山poi_order=1到目前poi_order=N總共時間(秒)
        6. avg_temp, avg_rh, max_precip -> 查詢他本次爬山poi_order=N-1到poi_order=N這段期間對應到天氣戰紀錄的平均氣溫, 累積降雨和相對溼度
        """
        # 解析傳入參數
        # parser = reqparse.RequestParser()
        # parser.add_argument("trail_id", type=int, required=True)
        # parser.add_argument("poi_id", type=int, required=True)
        # parser.add_argument("poi_order", type=int, required=True)
        # data = parser.parse_args()
        data = {"trail_id": 1, "poi_id": 12, "poi_order": 2}
        # 查詢Redis與fallback機制

        try:
            # feature包裝
            features = Features(
                avg_temp=8.9,
                avg_rh=7,
                max_precip=1000,
                distance=1713,
                elevation_range=526.2,
                elevation_change=-304.5,
                elevation_gain=19,
                elevation_loss=539.8,
                high_elevation=1,
                max_slope_percent=-74.2,
                max_slope_degrees=-36.55,
                slope_std_dev=10.57,
                slope_variance=111.64,
                max_slope_lat=24.412,
                max_slope_lon=121.309677,
                slope_neg15=67.27,
                slope_neg15_neg10=14.55,
                slope_neg10_neg5=3.64,
                slope_neg5_neg1=3.88,
                slope_neg1_1=3.64,
                slope_1_5=5.45,
                slope_5_10=1.82,
                slope_10_15=0,
                slope_over15=3,
                accumulated_time_seconds=30580,
                accumulated_distance=9813.28,
            )
            TIME_PREDICTION_HOST = os.getenv("TIME_PREDICTION_HOST")
            TIME_PREDICTION_PORT = os.getenv("TIME_PREDICTION_PORT")
            # 本機開發測試
            # TIME_PREDICTION_HOST = "localhost"
            # TIME_PREDICTION_PORT = 8000
            Request_url = (
                f"http://{TIME_PREDICTION_HOST}:{TIME_PREDICTION_PORT}/predict"
            )
            print("Request Url:", Request_url)
            response = req.post(Request_url, data=json.dumps(features.dict()))
            result = response.json()
            predicted_result = result["predicted_spend_time_seconds"]
            print("Backend returns: ", predicted_result)

            return {
                "message": "成功接收預測模型回傳結果",
                "result": predicted_result,
            }, 200
        except Exception as e:
            return {"message": "伺服器錯誤", "error": str(e)}, 500
