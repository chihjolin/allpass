from flask_restful import Resource
from flask import jsonify
import json
import os
from pathlib import Path

current_path = Path(__file__).resolve()
json_path = current_path.parents[2] / 'frontend' / 'data' / 'map_cood.json'

class Map(Resource):
#@app.route('/api/map/coordinates') # 地圖座標點(通訊站)
    def get(self):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)