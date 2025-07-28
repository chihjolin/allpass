from dotenv import load_dotenv
import os
import json
from pathlib import Path
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
#from utils.sql import Trails, TrailStats

load_dotenv()  # 讀取 .env 檔

def con_to_db():
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print(DATABASE_URL)
    engine = create_engine(DATABASE_URL)
    try:
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        print("✅ 成功連線 PostgreSQL")
        return conn
        #conn.close()
    except Exception as e:
        print("❌ 連線失敗:", e)



def get_db_data():
    trails = session.query(Trail).all()
    result = []
    for t in trails:
        result.append({
            "id": t.id,
            "name": t.name,
            "location": t.location,
            "difficulty": t.difficulty,
            "permitRequired": t.permit_required,
            "planningPageUrl": t.planning_page_url,
            "stats": {
                "totalTime": f"{t.stats.total_time} 小時",
                "distance": f"{t.stats.distance_km} 公里",
                "ascent": f"{t.stats.ascent_m} 公尺",
                "descent": f"{t.stats.descent_m} 公尺"
            },
            "weatherStation": {
                "locationName": t.weather_station
            }
        })
    session.close()
    return jsonify({"trails": result})