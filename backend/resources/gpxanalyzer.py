from flask_restful import Resource
from flask import jsonify, request
import json
import os
#from utils.db import get_db_data
#import requests as req
import gpxpy
import gpxpy.gpx
from datetime import timedelta

class GpxAnalyzer(Resource):
    def post(self):
        if 'gpxFile' not in request.files:
            return jsonify({'message': '沒有找到上傳的檔案'}), 400
        
        file = request.files['gpxFile']
        if file.filename == '':
            return jsonify({'message': '沒有選擇檔案'}), 400
        
        #使用者完成登山後上傳完整的gpx, 作為新的訓練資料來源
        #解析gpx並將特徵存入postgres(user_gpx.test)


        try:
            gpx_content = file.read().decode('utf-8')
            gpx = gpxpy.parse(gpx_content)
            
            moving_data = gpx.get_moving_data()
            uphill, downhill = gpx.get_uphill_downhill()
            summary = {
                "totalTime": f"{int(moving_data.moving_time // 3600)} 小時 {int((moving_data.moving_time % 3600) // 60)} 分鐘",
                "distance": f"{gpx.length_3d() / 1000:.2f} 公里",
                "ascent": f"{uphill:.0f} 公尺", "descent": f"{downhill:.0f} 公尺"
            }

            timeline_points = []
            if gpx.waypoints:
                for point in gpx.waypoints:
                    timeline_points.append({
                        "name": point.name or "未命名航點",
                        "time": point.time.strftime('%H:%M') if point.time else None,
                        "elevation": f"H {point.elevation:.0f} m" if point.elevation else ""
                    })
            else:
                all_points_with_indices = list(gpx.walk())
                if all_points_with_indices:
                    sample_interval = timedelta(minutes=30)
                    
                    start_point_tuple = all_points_with_indices[0]
                    start_point = start_point_tuple[0] # 🔧 修正：從元組中取出 point 物件
                    timeline_points.append({
                        "name": "開始行程",
                        "time": start_point.time.strftime('%H:%M') if start_point.time else None,
                        "elevation": f"H {start_point.elevation:.0f} m" if start_point.elevation else ""
                    })

                    if start_point.time:
                        next_sample_time = start_point.time + sample_interval
                        for point_tuple in all_points_with_indices:
                            point = point_tuple[0] # 🔧 修正：從元組中取出 point 物件
                            if point.time and point.time >= next_sample_time:
                                timeline_points.append({
                                    "name": "行程中",
                                    "time": point.time.strftime('%H:%M'),
                                    "elevation": f"H {point.elevation:.0f} m" if point.elevation else ""
                                })
                                next_sample_time += sample_interval
                    
                    end_point_tuple = all_points_with_indices[-1]
                    end_point = end_point_tuple[0] # 🔧 修正：從元組中取出 point 物件
                    if not timeline_points or (end_point.time and timeline_points[-1]['time'] != end_point.time.strftime('%H:%M')):
                        timeline_points.append({
                            "name": "結束行程",
                            "time": end_point.time.strftime('%H:%M') if end_point.time else None,
                            "elevation": f"H {end_point.elevation:.0f} m" if end_point.elevation else ""
                        })

            result = { "summary": summary, "waypoints": timeline_points }
            return jsonify(result)
                

        except Exception as e:
            print(f"GPX 解析錯誤: {e}")
            return jsonify({'message': f"GPX 檔案解析失敗: {e}"}), 500


