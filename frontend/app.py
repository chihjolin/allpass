import os
import json
from flask import Flask, jsonify, send_from_directory, request, send_file
from flask_cors import CORS
import requests
import gpxpy
import gpxpy.gpx
import io
import zipfile
import threading

# --- 初始化 Flask 應用 ---
app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app) 

# --- 設定 ---
CWA_API_KEY = '在這裡貼上氣象局 API KEY' # ⚠️ 替換成自己的金鑰
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'database.json')

# --- 幫助函式：讀取資料庫 ---
def get_db_data():
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# --- 原有 API 路由 (Routes) ---

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/trails', methods=['GET'])
def get_trails():
    data = get_db_data()
    return jsonify(data.get('trails', []))

@app.route('/api/trails/<string:trail_id>', methods=['GET'])
def get_trail_by_id(trail_id):
    data = get_db_data()
    trails = data.get('trails', [])
    trail = next((t for t in trails if t['id'] == trail_id), None)
    if trail:
        return jsonify(trail)
    else:
        return jsonify({'message': '找不到該步道'}), 404

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

# --- ✨ API 路由：處理 GPX 上傳與分析 ---
@app.route('/api/gpx/analyze', methods=['POST'])
def analyze_gpx():
    if 'gpxFile' not in request.files:
        return jsonify({'message': '沒有找到上傳的檔案'}), 400

    file = request.files['gpxFile']

    if file.filename == '':
        return jsonify({'message': '沒有選擇檔案'}), 400

    try:
        # 為了能重複讀取，先讀入記憶體
        gpx_content = file.read().decode('utf-8')
        gpx = gpxpy.parse(gpx_content)

        # 計算數據
        moving_data = gpx.get_moving_data()
        uphill, downhill = gpx.get_uphill_downhill()

        result = {
            "totalTime": f"{int(moving_data.moving_time // 3600)} 小時 {int((moving_data.moving_time % 3600) // 60)} 分鐘",
            "distance": f"{moving_data.moving_distance / 1000:.2f} 公里",
            "ascent": f"{uphill:.0f} 公尺",
            "descent": f"{downhill:.0f} 公尺"
        }
        return jsonify(result)

    except Exception as e:
        print(f"GPX 解析錯誤: {e}")
        return jsonify({'message': f'GPX 檔案解析失敗: {e}'}), 500
    
# --- ✨ 地圖處理 ---
@app.route('/api/map/coordinates') # 地圖座標點(通訊站)
def get_geojson():
    with open(r'data\map_cood.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/api/tiles/download', methods=['POST'])
def download_tiles():
    """
    前端傳入: {
        "tiles": [
            {"z": 15, "x": 27345, "y": 13456},
            ...
        ]
    }
    回傳: zip檔, 內容為 /z/x/y.png
    """
    data = request.get_json()
    tiles = data.get('tiles', [])
    if not tiles:
        return jsonify({'message': '未提供圖磚座標'}), 400

    # 限制單次請求最多 100 張
    if len(tiles) > 100:
        return jsonify({'message': '單次請求圖磚數量過多，請縮小範圍或分批下載'}), 400

    tile_url_tpl = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    headers = {
        "User-Agent": "HikingAppTileDownloader/1.0 (your_email@example.com)"
    }

    mem_zip = io.BytesIO()
    found_any = False
    errors = []

    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for t in tiles:
            z, x, y = t['z'], t['x'], t['y']
            url = tile_url_tpl.format(z=z, x=x, y=y)
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    zf.writestr(f"{z}/{x}/{y}.png", resp.content)
                    found_any = True
                    print(f"成功下載: {url}")
                else:
                    errors.append(f"下載失敗: {url} 狀態碼: {resp.status_code}")
            except Exception as e:
                errors.append(f"例外: {url} {e}")
                print("下載圖磚失敗:", url, e)

    mem_zip.seek(0)

    if not found_any:
        print("全部圖磚下載失敗:", errors)
        return jsonify({'message': '圖磚全部下載失敗，請稍後再試。', 'errors': errors}), 500

    if errors:
        print("部分圖磚下載失敗:", errors)

    return send_file(
        mem_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name='tiles.zip'
    )

# --- 啟動伺服器 ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)