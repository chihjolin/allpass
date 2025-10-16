import json
import os
import uuid
from datetime import datetime

import requests as req
from flask import request
from flask_restful import Resource, reqparse
from pydantic import BaseModel
from sqlalchemy import text

from common.utils.dbcon import engine
from common.utils.redis_utils import (
    get_segment_features,
    get_session_uuid,
    set_session_uuid,
)

# class Features(BaseModel):
#     avg_temp: float
#     avg_rh: float
#     max_precip: float
#     distance: float
#     elevation_range: float
#     elevation_change: float
#     elevation_gain: float
#     elevation_loss: float
#     high_elevation: float
#     max_slope_percent: float
#     max_slope_degrees: float
#     slope_std_dev: float
#     slope_variance: float
#     max_slope_lat: float
#     max_slope_lon: float
#     slope_neg15: float
#     slope_neg15_neg10: float
#     slope_neg10_neg5: float
#     slope_neg5_neg1: float
#     slope_neg1_1: float
#     slope_1_5: float
#     slope_5_10: float
#     slope_10_15: float
#     slope_over15: float
#     accumulated_time_seconds: float
#     accumulated_distance: float


# TIME_PREDICTION_HOST = os.getenv("TIME_PREDICTION_HOST")
# TIME_PREDICTION_PORT = os.getenv("TIME_PREDICTION_PORT")
# 本機開發測試
TIME_PREDICTION_HOST = "localhost"
TIME_PREDICTION_PORT = 8000


def parse_datetime(value: str):
    """ISO8601 轉 datetime"""
    try:
        return datetime.fromisoformat(value)
    except Exception:
        raise ValueError("Invalid datetime format, expected ISO8601")


class Predictions(Resource):
    def post(self):
        """
        功能: 接收使用者行進當下時間,封裝特徵,傳給模型服務並將模型預測結果(time_spend_seconds)傳回給前端
        1. 取得trail_id, poi_id, poi_order, datetime(ISO8601格式字串"2025-08-29T14:30:00+08:00"), user_id
        2. 寫進postgres:poi_visit_records
        3. 目前進度查詢:取得next_poi_id及還剩下幾個通訊點 -> 決定回傳幾段預測時間(秒)
        4. key: (trail_id + poi_c_id + poi_n_id)查該路段地形特徵(Redis)
        5. accumulated_time_seconds -> 查詢並計算他本次爬山poi_order=1到目前poi_order=N總共時間(秒)
        6. avg_temp, avg_rh, max_precip -> 查詢他本次爬山poi_order=N-1到poi_order=N這段期間對應到天氣戰紀錄的平均氣溫, 累積降雨和相對溼度
        7. 封裝特徵
        8. 呼叫時間預測模型服務，取得模型預測時間並傳回給前端
        """
        try:
            # # ===1. 解析傳入參數===
            # # parser = reqparse.RequestParser()
            # # parser.add_argument("trail_id", type=int, required=True)
            # # parser.add_argument("poi_id", type=int, required=True)
            # # parser.add_argument("poi_order", type=int, required=True)
            # # parser.add_argument("user_id", type=str, required=True)
            # # parser.add_argument("datetime", type=str, required=True)
            # # data = parser.parse_args()
            # # 測試用
            # data = {
            #     "trail_id": 1,
            #     "poi_id": 1,
            #     "poi_order": 1,
            #     "user_id": 1,
            #     "datetime": "2025-08-29T14:30:00+08:00",
            # }
            # trail_id = data["trail_id"]
            # poi_id = data["poi_id"]
            # poi_order = data["poi_order"]
            # user_id = data["user_id"]
            # recorded_at = parse_datetime(data["datetime"])
            # date_str = recorded_at.strftime("%Y%m%d")

            # # data_new = {"trail_id": 3, "current_poi_id": 12, "next_poi_id": 1}

            # # ===2. 寫進poi_visit_records ===
            # if poi_order == 1:
            #     # 產生新的session_uuid寫進redis一筆
            #     session_uuid = str(uuid.uuid4())
            #     set_session_uuid(trail_id, user_id, date_str, session_uuid)
            # else:
            #     # 從redis查詢本次爬山session_uudi
            #     session_uuid = get_session_uuid(trail_id, user_id, date_str)
            #     if not session_uuid:
            #         return {"message": "Session not found"}, 400
            # insert_query = """
            #     INSERT INTO user_gpx.poi_visit_records (session_uuid, user_id, trail_id, poi_id, poi_order, recorded_at)
            #     VALUES(:session_uuid, :user_id, :trail_id, :poi_id, :poi_order, :recorded_at);
            #     """
            # with engine.begin() as conn:
            #     conn.execute(
            #         text(insert_query),
            #         {
            #             "session_uuid": session_uuid,
            #             "user_id": user_id,
            #             "trail_id": trail_id,
            #             "poi_id": poi_id,
            #             "poi_order": poi_order,
            #             "recorded_at": recorded_at,
            #         },
            #     )

            # # ===3. 目前進度查詢：　取得next_poi_id及還剩下幾個通訊點 ===
            # query_sql = """"""

            # # ===4. key: (trail_id + poi_c_id + poi_n_id)查該路段地形特徵(Redis) ===
            # # 查詢Redis與fallback機制
            # geo_features = get_segment_features(
            #     int(data["trail_id"]),
            #     int(data["current_poi_id"]),
            #     int(data["next_poi_id"]),
            # )
            # print(geo_features)
            # return geo_features, 200
            # ===5. 計算本次爬行到目前的累計時間: accumulated_time_seconds===
            # ===6. 查詢本段路徑行徑間天氣狀況:avg_temp, avg_rh, max_precip===
            # ===7. 封裝特徵 ===

            features = {
                "avg_temp": 3,
                "avg_rh": 7,
                "max_precip": 1000,
                "distance": 1713,
                "elevation_range": 526.2,
                "elevation_change": -304.5,
                "elevation_gain": 19,
                "elevation_loss": 539.8,
                "high_elevation": 1,
                "max_slope_percent": -74.2,
                "max_slope_degrees": -36.55,
                "slope_std_dev": 10.57,
                "slope_variance": 111.64,
                "max_slope_lat": 24.412,
                "max_slope_lon": 121.309677,
                "slope_neg15": 67.27,
                "slope_neg15_neg10": 14.55,
                "slope_neg10_neg5": 3.64,
                "slope_neg5_neg1": 3.88,
                "slope_neg1_1": 3.64,
                "slope_1_5": 5.45,
                "slope_5_10": 1.82,
                "slope_10_15": 0,
                "slope_over15": 3,
                "accumulated_time_seconds": 30580,
                "accumulated_distance": 9813.28,
            }

            # ===8. 呼叫時間預測模型服務，取得模型預測時間並傳回給前端 ===
            Request_url = (
                f"http://{TIME_PREDICTION_HOST}:{TIME_PREDICTION_PORT}/predict"
            )
            print("Request Url:", Request_url)
            response = req.post(Request_url, data=json.dumps(features))
            result = response.json()
            predicted_result = result["predicted_spend_time_seconds"]
            print("Backend returns: ", predicted_result)

            return {
                "message": "成功接收預測模型回傳結果",
                "result": predicted_result,
            }, 200
        except Exception as e:
            return {"message": "伺服器錯誤", "error": str(e)}, 500
