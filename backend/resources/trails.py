from flask_restful import Resource
from flask import jsonify
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from utils.dbcon import SessionLocal
from models import TrailModel, POIModel

class Trails(Resource):
    def get(self):
        """
        傳回所有官方路徑基本資料
        """
        try:
            with SessionLocal() as session:
                trails = session.query(TrailModel).all()
                result = []
                for t in trails:
                    result.append({
                        "id": t.trail_id,
                        "name": t.name,
                        "location": t.location,
                        "difficulty": t.difficulty,
                        "permitRequired": t.permit_required,
                        # "stats": {
                        #     "totalTime": f"{t.estimated_duration_h} 小時",
                        #     "distance": f"{t.length_km} 公里",
                        #     "ascent": f"{t.elevation_gain_m} 公尺",
                        #     "descent": f"{t.descent_m} 公尺"
                        # },
                        # "weatherStation": {
                        #     "locationName": t.weather_station
                        # }
                    })
            return jsonify({"trails": result})
        except Exception as e:
            return jsonify({"message": "伺服器錯誤", "error": str(e)}), 500
    
class Trail(Resource):
    def get(self, id):
        """
        傳回特定id的官方路徑詳細資料
        """
        try: 
            with SessionLocal() as session:
                trail = session.query(TrailModel).filter_by(trail_id = id).first()
                if not trail:
                    return jsonify({"message": "找不到該步道"}), 404
                trail_properties = {
                            "id": trail.trail_id,
                            "name": trail.name,
                            "location": trail.location,
                            "difficulty": trail.difficulty,
                            "permitRequired": trail.permit_required,
                            "stats": {
                                "totalTime": f"{trail.estimated_duration_h} 小時",
                                "distance": f"{trail.length_km} 公里",
                                "ascent": f"{trail.elevation_gain_m} 公尺",
                                "descent": f"{trail.descent_m} 公尺"
                            },
                            "weatherStation": {
                                "locationName": trail.weather_station
                            }
                    }
            return (jsonify(trail_properties),200)               
        except Exception as e:
            return jsonify({"message": "伺服器錯誤", "error": str(e)}), 500
        
class Trailgeo(Resource):
    def get(self, id):
        """
        以GEOJSON格式傳回特定id的官方路徑地理資料（路線+各通訊點）
        """
        features = []
        try:
            
            with SessionLocal() as session:                
                trail = session.query(TrailModel).filter_by(trail_id=id).first()
                #轉換成GeoJSON
                trail_linestring_geom = mapping(to_shape(trail.route_geometry)) if trail else None  
                features.append(
                    {
                        "type":"Feature",
                        "geometry": trail_linestring_geom,
                        "properties": {
                            "type": "route",
                            "id": trail.trail_id
                        }
                    }
                )
                point_records = session.query(POIModel).filter_by(trail_id = id).all()
                for pt in point_records:
                    pt_geom = mapping(to_shape(pt.location))
                    features.append(
                        {
                            "type":"Feature",
                            "geometry": pt_geom,
                            "properties": {
                                "type": "point",
                                "name": pt.name
                            }
                        }
                    )

            feature_collection = {
                "type": "FeatureCollection",
                "features" :features
            }
            return jsonify(feature_collection), 200

        except Exception as e:
            return jsonify({"message": "伺服器錯誤", "error": str(e)}), 500           

        #trails = get_all_trails_data()
        #trails = data.get('trails', [])
        #trail = next((t for t in trails if t['id'] == id), None)

        #從Postgres/Redis取得目標trail的linestring和points(ROI), 包成GeoJSON格式傳回給前端
        """
        # 建立主路線
        route_line = LineString([(p.longitude, p.latitude) for p in all_points])

        # 通訊點
        comm_points = [Point(p.longitude, p.latitude) for p in extracted_comm_points]

        # 建立 GeoJSON 結構
        geojson_obj = {
            "type": "FeatureCollection",
            "features": []
        }

        # 加入路線
        geojson_obj["features"].append({
            "type": "Feature",
            "properties": {"type": "route"},
            "geometry": mapping(route_line)
        })

        # 加入每個通訊點（可加入名稱、序號等）
        for idx, pt in enumerate(comm_points, start=1):
            geojson_obj["features"].append({
                "type": "Feature",
                "properties": {
                    "type": "comm_point",
                    "id": f"cp{idx}",
                    "label": f"通訊點{idx}"
                },
                "geometry": mapping(pt)
            })

        # 輸出 GeoJSON
        geojson_str = json.dumps(geojson_obj, ensure_ascii=False, indent=2)

        """

        if trail:
            return jsonify(trail)
        else:
            return jsonify({'message': '找不到該步道'}), 404