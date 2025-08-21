from flask_restful import Resource
from sqlalchemy import text
from geoalchemy2.shape import to_shape
#from models import POIModel, TrailModel
from shapely.geometry import mapping
from utils.dbcon import SessionLocal, engine
from utils.dbcon import engine


class Trails(Resource):
    def get(self):
        """
        傳回所有官方路徑基本資料
        """
        try:
            with engine.connect() as conn:
                query_sql = """
                    SELECT id, trail_name_ch, location_name, permit_required from paths.trails ORDER BY id
                """
                trails = conn.execute(text(query_sql)).all()
                result = [
                    {
                        "id":t.id, 
                        "name": t.trail_name_ch,
                        "location": t.location_name,
                        "difficulty": "-", 
                        "permitRequired": t.permit_required
                    }
                    for t in trails]
            return {"message": "成功查到所有步道基本資料", "trails": result}, 200
        except Exception as e:
            return {"message": "伺服器錯誤", "error": str(e)}, 500


class Trail(Resource):
    def get(self, id):
        """
        傳回特定id的官方路徑詳細資料
        """
        try:
            features = []
            with engine.connect() as conn:
                #路線與氣象站詳細資料
                query_sql = """
                    SELECT 
                        t.id AS trail_id,
                        t.trail_name_ch,
                        t.location_name,
                        t.permit_required,
                        t.length_km,
                        t.elevation_start_m,
                        t.elevation_end_m,
                        json_agg(DISTINCT jsonb_build_object(
                            'station_id', s.id,
                            'station_code', s.station_code,
                            'station_name', s.station_name,
                            'station_geolocation', s.geolocation
                        )) AS stations
                    FROM paths.trails t
                    LEFT JOIN paths.trail_stations ts ON t.id = ts.trail_id
                    LEFT JOIN weather.stations s ON ts.station_id = s.id
                    WHERE t.id = :trail_id
                    GROUP BY t.id, t.trail_name_ch;
                    """
                trail = conn.execute(text(query_sql), {"trail_id": id}).first()
            #with SessionLocal() as session:
                # trail = session.query(TrailModel).filter_by(trail_id=id).first()
                if not trail:
                    return {"message": "找不到該步道"}, 404
                # postgis(wkb) -> shapely(linestring) -> GeoJSON
                trail_geom = mapping(to_shape(trail.route_geometry))
                # 建立路徑feature
                features.append(
                    {
                        "type": "Feature",
                        "geometry": trail_geom,
                        "properties": {
                            "id":trail.id, 
                            "name": trail.trail_name_ch,
                            "location": trail.location_name,
                            "permitRequired": trail.permit_required,
                            "length_km": f"{trail.length_km} 公里",
                            "elevation_start_m": f"起始海拔{trail.elevation_start_m} 公尺",
                            "elevation_end_m": f"最高海拔{trail.elevation_end_m} 公尺",
                            "weatherStation": [{
                                "id": trail.station_id,
                                "code": trail.station_code,
                                "name": trail.station_name}]
                        },
                    }
                )
                # point_records = session.query(POIModel).filter_by(trail_id=id).all()
                # for pt in point_records:
                #     pt_geom = mapping(to_shape(pt.location))
                #     # 建立通訊點feature
                #     features.append(
                #         {
                #             "type": "Feature",
                #             "geometry": pt_geom,
                #             "properties": {
                #                 "type": pt.poi_type,
                #                 "id": pt.poi_id,
                #                 "name": pt.name,
                #                 "order": pt.poi_order,
                #                 "description": pt.description,
                #             },
                #         }
                #     )

            feature_collection = {"type": "FeatureCollection", "features": features}
            return feature_collection, 200
        except Exception as e:
            return {"message": "伺服器錯誤", "error": str(e)}, 500

