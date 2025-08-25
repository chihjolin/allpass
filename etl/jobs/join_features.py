import json
import os

import geopandas as gpd
import pandas as pd
from shapely import wkb
from shapely.geometry import Point
from sqlalchemy import text

from common.utils.dbcon import engine


def run_join_features_job():
    """
    執行 join_features ETL job:
    - 從 raw table 讀取資料
    - 計算特徵
    - 寫入特徵表
    """

    # ===== 參數設定 =====
    data_folder = os.path.join(os.path.dirname(__file__), "data")
    # data_folder = "./jobs"
    csv_path = f"{data_folder}/feature_data_new.csv"
    table_name = "time_prediction"

    # ===== 1. 讀取 CSV =====
    df = pd.read_csv(csv_path)
    df.columns = [c.lower() for c in df.columns]  # 欄位名稱轉小寫

    # ===== 2. 連 PostgreSQL 取 POI 對照表並轉換WKB=====
    # 假設 wkb_hex 是從 DB 拿到的字串
    def wkb_to_point(wkb_hex):
        if wkb_hex is None:
            return None
        return wkb.loads(bytes.fromhex(wkb_hex))

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, geolocation FROM paths.points_of_interest;")
        )
        rows = result.fetchall()  # 取出所有資料
        # print(f"共 {len(rows)} 筆資料")
        # print(rows[:5])  # 先看前 5 筆

    poi_dict = {row.id: wkb_to_point(row.geolocation) for row in rows}
    # print(poi_dict)

    # ===== 3. 定義 WKT 轉 shapely Point =====
    def parse_point(raw_point):
        if pd.isna(raw_point):
            return None
        raw_point = (
            str(raw_point)
            .replace("POINT", "")
            .replace("(", "")
            .replace(")", "")
            .strip()
        )
        lat, lon = map(float, raw_point.split(","))
        return Point(lon, lat)

    # ===== 4. POI mapping =====
    # 假設 CSV 裡有 current_poi_id, next_poi_id 欄位
    df["current_poi_geo"] = df["current_poi_id"].map(poi_dict)
    df["next_poi_geo"] = df["next_poi_id"].map(poi_dict)

    # print(df["current_poi_geo"].head())

    # ===== 5. max_slope_point 轉 shapely =====
    df["max_slope_point"] = df["max_slope_point"].apply(parse_point)

    # ===== 6. slope_freq_dist 清理 =====
    df["slope_freq_dist"] = df["slope_freq_dist"].apply(
        lambda x: (
            json.dumps(json.loads(x.replace("'", '"')), ensure_ascii=False)
            if isinstance(x, str)
            else None
        )
    )

    # ===== 7. 統一時間單位（分鐘 float） =====
    df["spend_time"] = pd.to_timedelta(df["spend_time"])
    df["accumulated_time"] = pd.to_timedelta(df["accumulated_time"])
    df["spend_time_m"] = df["spend_time"].dt.total_seconds() / 60
    df["accumulated_time_m"] = df["accumulated_time"].dt.total_seconds() / 60

    # ===== 8. 創建 GeoDataFrame =====
    # GeoDataFrame 只能有一個 active geometry，我們選 next_poi_geo
    gdf = gpd.GeoDataFrame(df, geometry="next_poi_geo", crs="EPSG:4326")

    # 其他 geometry 欄位仍保留
    gdf["current_poi_geo"] = df["current_poi_geo"]
    gdf["max_slope_point"] = df["max_slope_point"]

    # ===== 9. 存入 PostgreSQL (含多個 geometry) =====
    # 注意：需要安裝 geopandas[sqlalchemy]，PostGIS 支援
    gdf.to_postgis(
        table_name, engine, schema="ml_features", if_exists="replace", index=False
    )
    print(f"✅ 資料已存入 {table_name}，包含三個 geometry 欄位")


if __name__ == "__main__":
    run_join_features_job()
