import os
import json
from pathlib import Path

#暫時以調檔模擬取db資料
current_path = Path(__file__).resolve()
db_path = current_path.parents[2] / "mock" / "database.json"

def get_db_data():
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)