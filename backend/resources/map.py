import json
import os
from pathlib import Path

from flask import jsonify
from flask_restful import Resource

current_path = Path(__file__).resolve()
json_path = current_path.parents[0] / "map_cood.json"

#從Postgres/Redis取得目標trail的linestring和points(ROI), 包成GeoJSON格式傳回給前端
class Map(Resource):
    # 地圖座標點(通訊站)
    def get(self):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
