from flask_restful import Resource
from flask import jsonify
from utils.sql import get_all_trails_data

class Trails(Resource):
    def get(self):
        data = get_all_trails_data()
        return jsonify({"trails": data})
    
class Trail(Resource):
    def get(self, id):
        trails = get_all_trails_data()
        #trails = data.get('trails', [])
        trail = next((t for t in trails if t['id'] == id), None)
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