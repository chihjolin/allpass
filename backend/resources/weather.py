from flask_restful import Resource
from flask import jsonify
import json
import os
#from utils.db import get_db_data
import requests as req
import certifi

CWA_API_KEY=os.getenv("CWA_API_KEY")
base_url = os.getenv("CWA_API_BASE")
endpoint = os.getenv("WEATHER_ENDPOINT")
url = f"{base_url}/{endpoint}"

class Weather(Resource):
    def get(self, location_name):
        #測試用(新北市)  
        location_name = "臺中市"   
        params = {
            "Authorization": CWA_API_KEY,
            "format": "JSON",
            "LocationName":location_name
        }
        try:
            response = req.get(url, params=params, verify=certifi.where())
            response.raise_for_status()
            data = response.json()
            try:
                weather_elements = data['records']['Locations'][0]['Location'][0]['WeatherElement']
            except:
                return jsonify({'message': '氣象局回傳資料格式異常'}), 500
            temp_el = next((item for item in weather_elements if item['ElementName'] == '平均溫度'), None)
            pop_el = next((item for item in weather_elements if item['ElementName'] == '12小時降雨機率'), None)
            wx_el = next((item for item in weather_elements if item['ElementName'] == '天氣現象'), None)
            if not all([temp_el, pop_el, wx_el]):
                 return jsonify({'message': '天氣資料欄位不完整'}), 500
            hourly_temp, hourly_pop, hourly_wx = temp_el['Time'], pop_el['Time'], wx_el['Time']
            formatted_weather = []
            for temp_time in hourly_temp:
                pop_entry = next((p for p in reversed(hourly_pop) if p['StartTime'] <= temp_time['StartTime']), None)
                wx_entry = next((w for w in reversed(hourly_wx) if w['StartTime'] <= temp_time['StartTime']), None)
                formatted_weather.append({
                    'time': temp_time['StartTime'], 'temp': temp_time['ElementValue'][0]['Temperature'],
                    'pop': pop_entry['ElementValue'][0]['ProbabilityOfPrecipitation'] if pop_entry else 'N/A',
                    'wx': wx_entry['ElementValue'][0]['Weather'] if wx_entry else 'N/A'
                    #'wxCode': wx_entry['ElementValue'][1]['value'] if wx_entry else 'N/A'
                
                })
            return jsonify(formatted_weather)
        except req.exceptions.RequestException as e:
            return jsonify({'message': '無法從氣象局獲取天氣資訊'}), 502
        except (KeyError, IndexError) as e:
            return jsonify({'message': '解析氣象局資料時發生錯誤'}), 500


"""
@app.route('/api/weather/<string:location_name>', methods=['GET'])
def get_weather(location_name):
    if not CWA_API_KEY or CWA_API_KEY == '在這裡貼上你的氣象局 API KEY':
        return jsonify({'message': '尚未設定氣象局 API 金鑰'}), 500
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091?Authorization={CWA_API_KEY}&format=JSON&locationName={location_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        weather_elements = data['records']['locations'][0]['location'][0]['weatherElement']
        temp_el = next((item for item in weather_elements if item['elementName'] == 'T'), None)
        pop_el = next((item for item in weather_elements if item['elementName'] == 'PoP12h'), None)
        wx_el = next((item for item in weather_elements if item['elementName'] == 'Wx'), None)
        if not all([temp_el, pop_el, wx_el]):
            return jsonify({'message': '天氣資料格式不完整'}), 500
        hourly_temp, hourly_pop, hourly_wx = temp_el['time'], pop_el['time'], wx_el['time']
        formatted_weather = []
        for temp_time in hourly_temp:
            pop_entry = next((p for p in reversed(hourly_pop) if p['startTime'] <= temp_time['startTime']), None)
            wx_entry = next((w for w in reversed(hourly_wx) if w['startTime'] <= temp_time['startTime']), None)
            formatted_weather.append({
                'time': temp_time['startTime'], 'temp': temp_time['elementValue'][0]['value'],
                'pop': pop_entry['elementValue'][0]['value'] if pop_entry else 'N/A',
                'wx': wx_entry['elementValue'][0]['value'] if wx_entry else 'N/A',
                'wxCode': wx_entry['elementValue'][1]['value'] if wx_entry else 'N/A'
            })
        return jsonify(formatted_weather[:24])
    except requests.exceptions.RequestException as e:
        return jsonify({'message': '無法從氣象局獲取天氣資訊'}), 502
    except (KeyError, IndexError) as e:
        return jsonify({'message': '解析氣象局資料時發生錯誤'}), 500
"""