from flask import request
from flask_restful import Resource

# 取得使用者行進當下時間(推論特徵), 傳給模型並返回模型預測結果


class Predictions(Resource):
    def post(self):
        """
        接收使用者行進當下時間, 推論特徵並返回模型預測結果
        """
        try:
            data = request.get_json()
            # 假設data包含必要的特徵
            # 這裡應該調用模型進行預測
            # 模型預測邏輯...
            prediction_result = {
                "message": "成功接收時間",
                "received_timestamp": data.get("timestamp"),
                "prediction": "2hr",  # 模型返回的結果
                "confidence": 0.95,  # 模型預測的置信度
            }
            return prediction_result, 200
        except Exception as e:
            return {"message": "伺服器錯誤", "error": str(e)}, 500
