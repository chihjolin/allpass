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
        if trail:
            return jsonify(trail)
        else:
            return jsonify({'message': '找不到該步道'}), 404