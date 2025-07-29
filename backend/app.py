import json
import os
from pathlib import Path

import gpxpy
import gpxpy.gpx
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restful import Api, Resource
from resources.gpxanalyzer import GpxAnalyzer
from resources.map import Map
from resources.tiles import Tiles
from resources.trails import Trail, Trails
from resources.weather import Weather

# --- 初始化 Flask 應用 ---
app = Flask(__name__)
# ---本機測試用---
# app = Flask(__name__, static_folder="../frontend/static", static_url_path="")
# app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)
api = Api(app)

# ---RESTful API ---
api.add_resource(Trails, "/api/trails")
api.add_resource(Trail, "/api/trails/<string:id>")
api.add_resource(Weather, "/api/weather/<string:location_name>")
api.add_resource(GpxAnalyzer, "/api/gpxanalyzer")
api.add_resource(Map, "/api/map/coordinates")
api.add_resource(Tiles, "/api/tiles/download")

# --- 啟動伺服器 ---
if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    debug = bool(os.getenv("FLASK_DEBUG", "TRUE"))
    app.run(host=host, port=port, debug=debug)
