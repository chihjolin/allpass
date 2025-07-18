from flask_restful import Resource
from flask import jsonify
import json
import os
from utils.db import get_db_data

class Trails(Resource):
    def get(self):
        data = get_db_data()
        return jsonify(data.get("trails", []))
