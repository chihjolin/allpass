# import sys
# print(sys.executable)
# print(sys.path)
# import importlib

import json

# importlib.reload(utils.dbcon)
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import geopandas as gpd
import gpxpy
import gpxpy.gpx
import pandas as pd
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import LineString, Point, mapping
from sqlalchemy import text

# from utils.dbcon import engine
from werkzeug.security import generate_password_hash

# import utils.dbcon
from common.utils.dbcon import engine


def main():
    """
    初始化 PostgreSQL 資料表，匯入 raw data
    返回 True 表示初始化成功
    """
    data_folder = os.path.join(os.path.dirname(__file__), "data")
    # data_folder = "./init/data"
    excel_path = f"{data_folder}/allpass_data_1.0.3.xlsx"
    tables = get_all_tables(engine)
    imported_tables = insert_data(excel_path, engine)
    print(f"已匯入資料的資料表:{imported_tables}")
    relation_path = f"{data_folder}/relation.xlsx"

    df_trail_station = pd.read_excel(relation_path, sheet_name="trail_station")

    # print(df_trail_station)
    # df_stations
    with engine.connect() as conn:
        query = "SELECT id, station_code from weather.stations"
        result = conn.execute(text(query))

    station_dict = {row.station_code: row.id for row in result}

    insert_trail_stations(df_trail_station, station_dict, engine)

    gpx_folder = Path(f"{data_folder}/gpx")
    insert_trail_geometry(gpx_folder, engine)

    weather_file = f"{data_folder}/weather_data.csv"
    insert_weather(weather_file, engine)

    poi_visit_records = f"{data_folder}/timing_results_0822.csv"
    insert_poi_visit_records(poi_visit_records, engine)

    feature_file = f"{data_folder}/feature_allfinal.csv"
    insert_trailseg_features(feature_file, engine)

    features = f"{data_folder}/feature_data_new.csv"

    return True  # 表示初始化成功


def get_all_tables(engine):
    query = """
        SELECT table_schema, table_name
        FROM information_schema.tables
        where table_type = 'BASE TABLE'
            AND table_schema not in ('pg_catalog', 'information_schema', 'public')
        ORDER BY table_schema, table_name;
    """

    with engine.connect() as conn:
        result = conn.execute(text(query))
        return [f"{row.table_schema}.{row.table_name}" for row in result]


def insert_data(excel_path, engine):
    sheets_dict = pd.read_excel(excel_path, sheet_name=None)
    # init初始化資料庫資料
    imported_tables = []
    for sheet_name, df in sheets_dict.items():
        schema_name, table_name = sheet_name.lower().replace(" ", "-").split(".")
        print(f"{schema_name}.{table_name}")

        # 移除不必要的欄位
        df = df.drop(
            columns=[c for c in ["id", "created_at", "updated_at"] if c in df.columns]
        )

        with engine.begin() as conn:  # 每張表獨立 transaction
            # 先清空舊資料
            conn.execute(
                text(
                    f"TRUNCATE TABLE {schema_name}.{table_name} RESTART IDENTITY CASCADE"
                )
            )

            # 再插入新資料
            df.to_sql(
                table_name,
                con=conn,
                schema=schema_name,
                if_exists="append",
                index=False,
            )

            imported_tables.append(f"{schema_name}.{table_name}")
            print(
                f"✅ Sheet [{sheet_name}] 已匯入到資料表 [{schema_name}.{table_name}]"
            )

    return imported_tables


def insert_trail_stations(df, station_dict, engine):
    """
    將 df 中的 trail 與 station 對應關係批次寫入 DB
    :param df: DataFrame，必須包含 trail_id, station1_id, station2_id 欄位
    :param station_dict: {station_code: station_id}
    :param engine: SQLAlchemy engine
    """

    insert_sql = """
    INSERT INTO paths.trail_stations (trail_id, station_id, priority)
    VALUES (:trail_id, :station_id, :priority)
    ON CONFLICT (trail_id, station_id) DO NOTHING
    """

    data_to_insert = []
    for trail in df.itertuples():
        station_1 = trail.station1_id
        station_2 = trail.station2_id

        for index, station in enumerate([station_1, station_2], start=1):
            if station in station_dict:  # 避免 station_dict 找不到 key
                data_to_insert.append(
                    {
                        "trail_id": trail.trail_id,
                        "station_id": station_dict[station],
                        "priority": index,
                    }
                )

    if not data_to_insert:
        print("⚠️ 沒有可插入的資料")
        return

    with engine.begin() as conn:
        conn.execute(text(insert_sql), data_to_insert)

    print(f"✅ 已批次寫入 {len(data_to_insert)} 筆 trail-station 關聯")


def insert_trail_geometry(gpx_folder, engine):
    with engine.connect() as conn:
        query_sql = "select id, trail_name_en from paths.trails"
        result = conn.execute(text(query_sql))

    trail_name_dict = {row.trail_name_en: row.id for row in result}

    update_sql = """
        UPDATE paths.trails
        SET route_geometry = ST_GeomFromText(:wkt, 4326)
        WHERE id = :trail_id
    """

    for gpx_file in gpx_folder.glob("*.gpx"):
        trail_id = trail_name_dict[gpx_file.stem]
        if not trail_id:
            print(f"  -> 找不到對應的 trail_id，略過 {gpx_file.name}")
            continue
        print(f"處理檔案:{gpx_file}-trail_id: {trail_id}")
        try:
            # 讀檔
            with open(gpx_file, "r", encoding="utf-8") as f:
                gpx_data = gpxpy.parse(f)

            # 假設只取第一個 track/segment 的點
            segment = gpx_data.tracks[0].segments[0]
            points = segment.points

            if not points:
                print(f"  -> 檔案 {gpx_file.name} 沒有點，略過")
                continue

            # 組成LineString 幾何格式
            coords = [(p.longitude, p.latitude) for p in points]
            linestring_new = LineString(coords)
            # print(linestring_new)
            wkt_str = linestring_new.wkt  # 轉成 WKT

            # 寫入資料庫: paths.trails
            with engine.begin() as conn:
                conn.execute(
                    text(update_sql),
                    {
                        "wkt": wkt_str,
                        "trail_id": trail_id,
                    },
                )

            print(f"✅ 已寫入{trail_id}-{gpx_file.stem} geometry")

        except Exception as e:
            print(f"❌ 錯誤處理 {gpx_file.name}：{e}")


def insert_weather(weather_file, engine):
    # weather
    # code_to_id
    with engine.connect() as conn:
        query_sql = "select id, station_code from weather.stations"
        result = conn.execute(text(query_sql))

    code_to_id = {row.station_code: row.id for row in result}
    print(code_to_id)

    # 寫入前先清空 weather.readings
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE weather.readings RESTART IDENTITY CASCADE;"))
        print("✅ 已清空 weather.readings")

    # csv -> weather.readings

    # 1. 讀取 CSV
    df = pd.read_csv(weather_file)

    # 2. 轉換 station code → station_id
    print(code_to_id)
    df["station_id"] = df["StationID"].map(code_to_id)

    # 3. 拆 DataTime
    df["DataTime"] = pd.to_datetime(df["DataTime"])
    df["recorded_date"] = df["DataTime"].dt.date
    df["recorded_time"] = df["DataTime"].dt.time

    # 4. rename 欄位 → 對應 schema
    df.rename(
        columns={
            "AirTemperature": "temperature_celsius",
            "RelativeHumidity": "humidity_percent",
            "Precipitation": "precipitation_mm",
        },
        inplace=True,
    )

    # 5. 固定來源 (可選)
    df["source"] = "CWB"
    df["weather_metadata"] = None  # 或 json.dumps({})

    # 6. 只取 schema 對應欄位
    insert_df = df[
        [
            "station_id",
            "recorded_date",
            "recorded_time",
            "temperature_celsius",
            "humidity_percent",
            "precipitation_mm",
            "source",
            "weather_metadata",
        ]
    ]

    # 7. 丟進資料庫
    insert_df.to_sql(
        "readings", engine, schema="weather", if_exists="append", index=False
    )


def insert_poi_visit_records(poi_visit_records, engine):

    # -----------------------------
    # 1️⃣ 設定 DB 連線
    # -----------------------------
    # DB_URI = "postgresql+psycopg2://username:password@localhost:5432/your_db"
    # engine = create_engine(DB_URI)

    # -----------------------------
    # 2️⃣ 讀取原始資料 (CSV)
    # -----------------------------
    # 假設欄位: trail_id, gpx_name, record_time, poi_id
    # 確保時間欄位是 datetime
    df = pd.read_csv(poi_visit_records)
    df["record_time"] = pd.to_datetime(df["record_time"], utc=True, format="mixed")
    # 去掉小數秒，保留 +00:00
    df["record_time"] = df["record_time"].dt.floor("S")
    df_str = df["record_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    # df = pd.read_csv("./data/timing_results_0820.csv", parse_dates=["record_time"])

    # -----------------------------
    # 3️⃣ 計算 session_order & poi_order
    # -----------------------------
    df["session_order"] = (
        df.groupby("trail_id")["gpx_name"].rank(method="dense").astype(int)
    )
    df["poi_order"] = (
        df.groupby("gpx_name")["record_time"].rank(method="first").astype(int)
    )
    df["nearest_time"] = df["record_time"].dt.round("H")

    # -----------------------------
    # 4️⃣ 建立使用者 (跨 trail)
    # -----------------------------
    session_orders = df["session_order"].unique()
    users_df = pd.DataFrame(
        {
            "email": [f"user{o}@example.com" for o in session_orders],
            "username": [f"user{o}" for o in session_orders],
            "password_hash": [
                generate_password_hash("password123") for _ in session_orders
            ],
        }
    )

    # 批次 insert users
    users_df.to_sql(
        "users",
        engine,
        schema="user_gpx",
        if_exists="append",
        index=False,
        method="multi",
    )

    # 取得 user_id 對應表
    user_map = pd.read_sql("SELECT id, username FROM user_gpx.users", engine)
    session_order_to_user = {
        int(row.username.replace("user", "")): row.id
        for idx, row in user_map.iterrows()
    }

    # -----------------------------
    # 5️⃣ 產生 gpx_uploads
    # -----------------------------
    gpx_uploads = []
    session_uuid_mapping = {}

    for gpx_name, group in df.groupby("gpx_name"):
        session_uuid = str(uuid.uuid4())
        session_order = group["session_order"].iloc[0]
        user_id = session_order_to_user[session_order]
        uploaded_at = group["record_time"].max()
        trail_id = group["trail_id"].iloc[0]

        gpx_uploads.append(
            {
                "session_uuid": session_uuid,
                "user_id": user_id,
                "file_name": gpx_name,
                "trail_id": trail_id,
                "uploaded_at": uploaded_at,
            }
        )
        session_uuid_mapping[gpx_name] = session_uuid

    gpx_uploads_df = pd.DataFrame(gpx_uploads)
    gpx_uploads_df.to_sql(
        "gpx_uploads",
        engine,
        schema="user_gpx",
        if_exists="append",
        index=False,
        method="multi",
    )

    # -----------------------------
    # 6️⃣ 對應 gpx_upload_id
    # -----------------------------
    gpx_map = pd.read_sql("SELECT id, session_uuid FROM user_gpx.gpx_uploads", engine)
    session_uuid_to_gpx_id = dict(zip(gpx_map["session_uuid"], gpx_map["id"]))

    # -----------------------------
    # 7️⃣ 產生 poi_visit_records
    # -----------------------------
    df["session_uuid"] = df["gpx_name"].map(session_uuid_mapping)
    df["gpx_upload_id"] = df["session_uuid"].map(session_uuid_to_gpx_id)
    df["user_id"] = df["session_order"].map(session_order_to_user)
    df["is_orphan_session"] = False

    poi_visit_df = df[
        [
            "session_uuid",
            "user_id",
            "gpx_upload_id",
            "trail_id",
            "poi_id",
            "poi_order",
            "record_time",
            "nearest_time",
            "is_orphan_session",
        ]
    ].copy()
    poi_visit_df.rename(columns={"record_time": "recorded_at"}, inplace=True)

    # 批次 insert poi_visit_records
    poi_visit_df.to_sql(
        "poi_visit_records",
        engine,
        schema="user_gpx",
        if_exists="append",
        index=False,
        method="multi",
    )

    print("✅ ETL 完成 (pandas.to_sql 批次 insert)")


def insert_trailseg_features(feature_file, engine):
    with engine.connect() as conn:
        query = """
            SELECT id, ST_AsBinary(geolocation) AS geom FROM paths.points_of_interest
        """
        result = conn.execute(text(query))

    poi_dict = {row.id: to_shape(WKBElement(row.geom, srid=4326)) for row in result}
    # print(poi_dict)
    # ===== 1. 讀取 CSV =====

    df = pd.read_csv(feature_file)

    # ===== 2. 欄位對應 =====
    column_mapping = {
        "trail_id": "trail_id",
        "route_folder": "trail_name_en",
        "filename": "filename",
        "part_number": "segment_order",
        "poi_previous_id": "current_poi_id",
        "poi_current_id": "next_poi_id",
        "distance": "distance",
        "elevation_range": "elevation_range",
        "elevation_change": "elevation_change",
        "elevation_gain": "elevation_gain",
        "elevation_loss": "elevation_loss",
        "high_elevation": "high_elevation",
        "max_slope": "max_slope_percent",
        "max_slope_degrees": "max_slope_degrees",
        "max_slope_point": "max_slope_point",
        "slope_std": "slope_std_dev",
        "slope_vari": "slope_variance",
        "slope_freq_dist": "slope_freq_dist",
        "accumulated_distance": "accumulated_distance",
    }

    df = df.rename(columns=column_mapping)
    # df["max_slope_point"].head(5)
    # df.loc[:4, "max_slope_point"]

    # ===== 3. 轉換 max_slope_point =====
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

    # ===== 5. 分別記錄max_slope_lat/lon以及max_slope_point 轉 shapely =====
    df["max_slope_lat"] = df["max_slope_point"].str.extract(r"\(([^,]+),").astype(float)
    df["max_slope_lon"] = (
        df["max_slope_point"].str.extract(r",\s*([^)]+)\)").astype(float)
    )
    df["max_slope_point"] = df["max_slope_point"].apply(parse_point)
    # df.loc[:4, "geometry"]

    # ===== 4. slope_freq_dist → JSONB =====
    # slope_freq_dist 字串（轉換為數值特徵）
    slope_dist = df["slope_freq_dist"].str.extract(
        r"'<-15°': ([^,]+), '-15°~-10°': ([^,]+), '-10°~-5°': ([^,]+), '-5°~-1°': ([^,]+), '-1°~1°': ([^,]+), '1°~5°': ([^,]+), '5°~10°': ([^,]+), '10°~15°': ([^,]+), '>15°': ([^}]+)"
    )
    df["slope_neg15"] = slope_dist[0].astype(float)
    df["slope_neg15_neg10"] = slope_dist[1].astype(float)
    df["slope_neg10_neg5"] = slope_dist[2].astype(float)
    df["slope_neg5_neg1"] = slope_dist[3].astype(float)
    df["slope_neg1_1"] = slope_dist[4].astype(float)
    df["slope_1_5"] = slope_dist[5].astype(float)
    df["slope_5_10"] = slope_dist[6].astype(float)
    df["slope_10_15"] = slope_dist[7].astype(float)
    df["slope_over15"] = slope_dist[8].astype(float)
    # (1) 先把字串轉成 dict
    df["slope_freq_dist"] = df["slope_freq_dist"].apply(
        lambda x: json.loads(x.replace("'", '"')) if isinstance(x, str) else None
    )

    # (2) 確保 insert 前再轉成 JSON 字串
    df["slope_freq_dist"] = df["slope_freq_dist"].apply(
        lambda x: json.dumps(x) if x is not None else None
    )

    # 處理 high_elevation 布林值
    df["high_elevation"] = df["high_elevation"].fillna(False).astype(int)

    # ===== 5. GeoDataFrame =====
    gdf = gpd.GeoDataFrame(df, geometry="max_slope_point", crs="EPSG:4326")

    # ===== 6. 寫入 PostGIS =====
    gdf.to_postgis(
        name="trail_segments",
        schema="ml_features",
        con=engine,
        if_exists="append",
        index=False,
    )


if __name__ == "__main__":
    main()
