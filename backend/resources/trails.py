import json

from flask_restful import Resource
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy import text

from common.utils.dbcon import engine

# from utils_dev.dbcon import engine


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
                        "id": t.id,
                        "name": t.trail_name_ch,
                        "location": t.location_name,
                        "difficulty": "-",
                        "permitRequired": t.permit_required,
                    }
                    for t in trails
                ]
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
                # 路線與氣象站詳細資料
                query_sql = """
                            SELECT 
                                t.id,
                                t.trail_name_ch,
                                t.location_name,
                                t.permit_required,
                                t.length_km,
                                t.elevation_start_m,
                                t.elevation_end_m,
                                ST_AsGeoJSON(t.route_geometry) AS route_geometry,
                                json_agg(jsonb_build_object(
                                    'station_id', s.id,
                                    'station_code', s.station_code,
                                    'station_name', s.station_name,
                                    'station_geolocation', s.geolocation
                                )) AS stations
                            FROM paths.trails t
                            LEFT JOIN (
                                SELECT DISTINCT ON (ts.trail_id) *
                                FROM paths.trail_stations ts
                                ORDER BY ts.trail_id, ts.priority ASC
                            ) ts ON t.id = ts.trail_id
                            LEFT JOIN weather.stations s ON ts.station_id = s.id
                            WHERE t.id = :trail_id
                            GROUP BY t.id;
                    """
                trail = conn.execute(text(query_sql), {"trail_id": id}).first()
                if not trail:
                    return {"message": "找不到該步道"}, 404

                station_1 = trail.stations[0]

                # station = json.loads(trail.stations) if trail.stations else []
                # postgis(wkb) -> shapely(linestring) -> GeoJSON
                # trail_geom = mapping(to_shape(trail.route_geometry))
                # trail_geom = mapping(wkt.loads(trail.route_geometry))
                geom = trail._mapping["route_geometry"]
                trail_geom = json.loads(geom)
                features = []
                # 建立路徑feature
                features.append(
                    {
                        "type": "Feature",
                        "geometry": trail_geom,
                        "properties": {
                            "id": trail.id,
                            "name": trail.trail_name_ch,
                            "location": trail.location_name,
                            "permitRequired": trail.permit_required,
                            "length_km": f"{trail.length_km} 公里",
                            "elevation_start_m": f"起始海拔{trail.elevation_start_m} 公尺",
                            "elevation_end_m": f"最高海拔{trail.elevation_end_m} 公尺",
                            "weatherStation": [
                                {
                                    "id": station_1["station_id"],
                                    "code": station_1["station_code"],
                                    "name": station_1["station_name"],
                                    "geolocation": station_1["station_geolocation"],
                                }
                            ],
                        },
                    }
                )
                query_sql = """
                        SELECT
                            t.id AS trail_id,
                            t.trail_name_ch AS trail_name,
                            COALESCE(
                            jsonb_agg(
                                jsonb_build_object(
                                'poi_id', p.id,
                                'poi_type', p.poi_type,
                                'poi_name', p.poi_name,
                                'poi_geo', ST_AsGeoJSON(p.geolocation)::jsonb,
                                'poi_order', tp.poi_order,
                                'description', p.description
                                )
                                ORDER BY tp.poi_order ASC
                            ),
                            '[]'::jsonb
                            ) AS pois
                        FROM paths.trail_pois tp
                        LEFT JOIN paths.points_of_interest p ON tp.poi_id = p.id
                        LEFT JOIN paths.trails t ON tp.trail_id = t.id
                        WHERE t.id = :trail_id
                        GROUP BY t.id, t.trail_name_ch;
                """
                result = conn.execute(text(query_sql), {"trail_id": trail.id}).first()
                # 從結果裡拿到 pois
                pois = result._mapping["pois"] or []

                # 保險處理：有些 driver 可能把 jsonb 當 str 回傳
                if isinstance(pois, str):
                    pois = json.loads(pois)

                # 遍歷每個 POI
                for pt in pois:
                    # 將 geojson 轉成 shapely geometry
                    pt_geom = pt.get("poi_geo")
                    # pt_geom = mapping(to_shape(pt["poi_geo"]))
                    features.append(
                        {
                            "type": "Feature",
                            "geometry": pt_geom,
                            "properties": {
                                "type": pt.get("poi_type"),
                                "id": pt.get("poi_id"),
                                "name": pt.get("poi_name"),
                                "order": pt.get(
                                    "poi_order"
                                ),  # 如果你在 SQL 裡沒選到，可以先填 None
                                "description": pt.get("description"),  # 同上
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
