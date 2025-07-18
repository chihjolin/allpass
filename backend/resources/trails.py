from flask_restful import Resource
from flask import jsonify
import json
import os
from utils.db import get_db_data

class Trails(Resource):
    def get(self):
        data = get_db_data()
        return jsonify(data.get("trails", []))
    
class Trail(Resource):
    def get(self, id):
        data = get_db_data()
        trails = data.get('trails', [])
        trail = next((t for t in trails if t['id'] == id), None)
        if trail:
            return jsonify(trail)
        else:
            return jsonify({'message': '找不到該步道'}), 404
