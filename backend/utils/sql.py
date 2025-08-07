from utils.dbcon import SessionLocal
from models.trail_model import TrailModel

def get_all_trails_data():
    session = SessionLocal()
    trails = session.query(TrailModel).all()
    result = []
    for t in trails:
        result.append({
            "id": t.trail_id,
            "name": t.name,
            "location": t.location,
            "difficulty": t.difficulty,
            "permitRequired": t.permit_required,
            "stats": {
                "totalTime": f"{t.estimated_duration_h} 小時",
                "distance": f"{t.length_km} 公里",
                "ascent": f"{t.elevation_gain_m} 公尺",
                "descent": f"{t.descent_m} 公尺"
            },
            "weatherStation": {
                "locationName": t.weather_station
            }
        })
    session.close()
    return result