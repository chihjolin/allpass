import io
import json
import os
import threading
import zipfile

import requests
from flask import jsonify, request, send_file
from flask_restful import Resource


class Tiles(Resource):
    def post(self):
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
        tiles = data.get("tiles", [])
        if not tiles:
            return jsonify({"message": "未提供圖磚座標"}), 400

        # 限制單次請求最多 100 張
        if len(tiles) > 100:
            return (
                jsonify({"message": "單次請求圖磚數量過多，請縮小範圍或分批下載"}),
                400,
            )

        tile_url_tpl = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        headers = {"User-Agent": "HikingAppTileDownloader/1.0 (your_email@example.com)"}

        mem_zip = io.BytesIO()
        found_any = False
        errors = []

        with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for t in tiles:
                z, x, y = t["z"], t["x"], t["y"]
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
            return (
                jsonify(
                    {"message": "圖磚全部下載失敗，請稍後再試。", "errors": errors}
                ),
                500,
            )

        if errors:
            print("部分圖磚下載失敗:", errors)

        return send_file(
            mem_zip,
            mimetype="application/zip",
            as_attachment=True,
            download_name="tiles.zip",
        )
