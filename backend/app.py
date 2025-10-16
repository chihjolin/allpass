import os

from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from resources.health import Health
from resources.login import Login
from resources.predictions import Predictions
from resources.profile import Profile
from resources.register import RegisterUser
from resources.tiles import Tiles
from resources.trails import Trail, Trails
from resources.weather import Weather

# from backend.resources.health import Health
# from backend.resources.login import Login
# from backend.resources.predictions import Predictions
# from backend.resources.register import RegisterUser
# from backend.resources.tiles import Tiles
# from backend.resources.trails import Trail, Trails
# from backend.resources.weather import Weather
# from backend.resources.profile import Profile

# --- 初始化 Flask App  ---
app = Flask(__name__)
CORS(app)
api = Api(app)


# --- 註冊API ---
api.add_resource(Health, "/health")  # 健康檢查路由
api.add_resource(Trails, "/api/trails")
# api.add_resource(Trail, "/api/trails/<string:id>")
api.add_resource(Trail, "/api/trails/<int:id>")
api.add_resource(Weather, "/api/weather/<string:location_name>")
api.add_resource(Tiles, "/api/tiles/download")
api.add_resource(Predictions, "/api/predictions")
api.add_resource(RegisterUser, "/api/register")
api.add_resource(Login, "/api/login")
api.add_resource(Profile, "/api/user-record/<int:id>")


# 測試一下
# @app.route("/api/time", methods=["POST"])
# def time():
#     data = request.get_json()
#     print(data)
#     return (
#         jsonify(
#             {"message": "成功接收時間", "received_timestamp": data.get("timestamp")}
#         ),
#         200,
#     )


# --- 啟動伺服器 ---
if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=5000, debug=True)
    port = int(os.getenv("FLASK_PORT", 5000))
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    debug = bool(os.getenv("FLASK_DEBUG", "TRUE"))
    app.run(host=host, port=port, debug=debug)
    # app.run(host=host, port=5050, debug=debug)
