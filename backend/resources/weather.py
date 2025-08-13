import json
import os

import certifi
import requests as req
from flask import jsonify
from flask_restful import Resource

CWA_API_KEY = os.getenv("CWA_API_KEY")
base_url = os.getenv("CWA_API_BASE")
endpoint = os.getenv("WEATHER_ENDPOINT")
url = f"{base_url}/{endpoint}"


class Weather(Resource):
    def get(self, location_name):
        # 測試用(新北市)
        location_name = "臺中市"
        params = {
            "Authorization": CWA_API_KEY,
            "format": "JSON",
            "LocationName": location_name,
        }
        try:
            response = req.get(url, params=params, verify=certifi.where())
            response.raise_for_status()
            data = response.json()
            try:
                weather_elements = data["records"]["Locations"][0]["Location"][0][
                    "WeatherElement"
                ]
            except:
                return {"message": "氣象局回傳資料格式異常"}, 500
            temp_el = next(
                (
                    item
                    for item in weather_elements
                    if item["ElementName"] == "平均溫度"
                ),
                None,
            )
            pop_el = next(
                (
                    item
                    for item in weather_elements
                    if item["ElementName"] == "12小時降雨機率"
                ),
                None,
            )
            wx_el = next(
                (
                    item
                    for item in weather_elements
                    if item["ElementName"] == "天氣現象"
                ),
                None,
            )
            if not all([temp_el, pop_el, wx_el]):
                return {"message": "天氣資料欄位不完整"}, 500
            hourly_temp, hourly_pop, hourly_wx = (
                temp_el["Time"],
                pop_el["Time"],
                wx_el["Time"],
            )
            formatted_weather = []
            for temp_time in hourly_temp:
                pop_entry = next(
                    (
                        p
                        for p in reversed(hourly_pop)
                        if p["StartTime"] <= temp_time["StartTime"]
                    ),
                    None,
                )
                wx_entry = next(
                    (
                        w
                        for w in reversed(hourly_wx)
                        if w["StartTime"] <= temp_time["StartTime"]
                    ),
                    None,
                )
                formatted_weather.append(
                    {
                        "time": temp_time["StartTime"],
                        "temp": temp_time["ElementValue"][0]["Temperature"],
                        "pop": (
                            pop_entry["ElementValue"][0]["ProbabilityOfPrecipitation"]
                            if pop_entry
                            else "N/A"
                        ),
                        "wx": (
                            wx_entry["ElementValue"][0]["Weather"]
                            if wx_entry
                            else "N/A"
                        ),
                        #'wxCode': wx_entry['ElementValue'][1]['value'] if wx_entry else 'N/A'
                    }
                )
            return formatted_weather, 200
        except req.exceptions.RequestException as e:
            return {"message": "無法從氣象局獲取天氣資訊"}, 502
        except (KeyError, IndexError) as e:
            return {"message": "解析氣象局資料時發生錯誤"}, 500
            return {"message": "解析氣象局資料時發生錯誤"}, 500
