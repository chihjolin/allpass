
-- 啟用 PostGIS 擴充套件
-- PostGIS 提供豐富的空間資料類型和函數，是處理地理資訊的核心。
CREATE EXTENSION IF NOT EXISTS postgis;

-- 建立三個核心 Schemas (資料庫模式/命名空間)
CREATE SCHEMA IF NOT EXISTS paths;      -- 存放官方/預定義的路徑與景點資料
CREATE SCHEMA IF NOT EXISTS user_gpx;   -- 存放使用者上傳的 GPX 軌跡資料
CREATE SCHEMA IF NOT EXISTS weather;    -- 存放天氣相關的觀測資料

-------------------------------------
-- Schema: paths (官方路徑資料與觀測點)
-------------------------------------
-- paths.trails: 儲存詳細的官方路徑資訊
CREATE TABLE paths.trails (
    id SERIAL PRIMARY KEY,                          -- 唯一識別碼，自動遞增
    baiyue_name VARCHAR(50),                        -- 百岳名稱，可為空
    name VARCHAR(100) NOT NULL UNIQUE,              -- 路徑名稱，必須唯一且非空
    difficulty SMALLINT,                            -- 難度等級，建議使用 1-5 等級標示
    distance_km NUMERIC(6, 2),                      -- 路徑總長度 (公里)，保留兩位小數
    total_ascent_m INT,                             -- 總爬升高度 (公尺)
    total_descent_m INT,                            -- 總下降高度 (公尺)
    total_time_h NUMERIC(5, 2),                     -- 估計完成時間 (小時)，保留兩位小數
    route_geometry GEOMETRY(LineString, 4326),      -- 路徑的地理幾何形狀，使用 LineString 類型和 WGS84 座標系 (EPSG:4326)
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 記錄建立時間，預設為當前時間帶時區
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄更新時間，預設為當前時間帶時區，由觸發器自動更新
);

-- paths.points_of_interest: 儲存路徑上的觀測點/興趣點 (POI)
-- 觀測點的類型 (poi_type) 可以是 '登山口', '營地', '山頂', '通訊點' 等。
CREATE TABLE paths.points_of_interest (
    id SERIAL PRIMARY KEY,                          -- 唯一識別碼
    trail_id INT REFERENCES paths.trails(id) ON DELETE CASCADE, -- 外鍵，關聯到 paths.trails 表，刪除路徑時一併刪除相關 POI
    name VARCHAR(100) NOT NULL,                     -- 觀測點名稱
    poi_type VARCHAR(50),                           -- 觀測點類型 (e.g., '山頂', '登山口', '通訊點')
    location GEOMETRY(PointZ, 4326) NOT NULL,       -- 觀測點的地理位置，使用 PointZ 類型儲存經度、緯度和海拔
    description TEXT,                               -- 詳細描述，用於補充說明
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 記錄建立時間
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄更新時間，由觸發器自動更新
);

-------------------------------------
-- Schema: user_gpx (使用者上傳的資料)
-------------------------------------
-- user_gpx.users: 儲存使用者基本資訊
CREATE TABLE user_gpx.users (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼，使用 BIGSERIAL 避免 ID 不足
    username VARCHAR(50) UNIQUE NOT NULL,           -- 使用者名稱，必須唯一且非空
    created_at TIMESTAMPTZ DEFAULT NOW()            -- 帳戶建立時間
);

-- user_gpx.gpx_uploads: 儲存使用者上傳的 GPX 檔案的摘要資訊
CREATE TABLE user_gpx.gpx_uploads (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼
    user_id BIGINT NOT NULL REFERENCES user_gpx.users(id) ON DELETE CASCADE, -- 外鍵，關聯到 user_gpx.users 表
    trail_id INT REFERENCES paths.trails(id),       -- 關聯到 paths.trails，允許為 NULL
    file_name VARCHAR(255) NOT NULL,                -- 原始 GPX 檔案名稱
    segment_name VARCHAR(255),                      -- 使用者為此路徑段提供的名稱
    total_distance_m NUMERIC(10, 2),                -- 總距離 (公尺)，從軌跡點計算而來
    total_duration_s INT,                           -- 總持續時間 (秒) 
    avg_speed_kmh NUMERIC(5, 2),                    -- 平均速度 (公里/小時) 
    start_time TIMESTAMPTZ,                         -- 軌跡開始時間 
    end_time TIMESTAMPTZ,                           -- 軌跡結束時間
    processing_status VARCHAR(20) DEFAULT 'pending', -- GPX 檔案的處理狀態 (e.g., 'pending', 'processed', 'failed')
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),          -- 檔案上傳到系統的時間
    gpx_route_geometry GEOMETRY(LineString, 4326)   -- 將使用者軌跡存為 LineString，方便空間查詢
);

-- user_gpx.gpx_track_points: 儲存 GPX 軌跡中的每一個點的詳細資訊
CREATE TABLE user_gpx.gpx_track_points (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼
    gpx_upload_id BIGINT NOT NULL REFERENCES user_gpx.gpx_uploads(id) ON DELETE CASCADE, -- 外鍵
    location GEOMETRY(PointZ, 4326) NOT NULL,       -- 軌跡點的地理位置 (經度、緯度、高程)，使用 PointZ 類型
    recorded_at TIMESTAMPTZ NOT NULL                -- 軌跡點記錄的時間

-------------------------------------
-- Schema: weather (天氣資料)
-------------------------------------
-- weather.stations: 儲存天氣站
CREATE TABLE weather.stations (
    id SERIAL PRIMARY KEY,                          -- 天氣站的唯一識別碼
    station_name VARCHAR(100) NOT NULL UNIQUE,      -- 天氣站名稱，必須唯一
    location GEOMETRY(Point, 4326) NOT NULL,        -- 天氣站的地理位置
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 記錄建立時間
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄更新時間
);

-- weather.readings: 儲存各個天氣站和時間的天氣觀測數據
-- 這是模型訓練的**核心特徵資料表**
CREATE TABLE weather.readings (
    id BIGSERIAL PRIMARY KEY,                       -- 觀測記錄的唯一識別碼
    station_id INT REFERENCES weather.stations(id), -- 外鍵，關聯到 weather.stations，實現正規化
    
    -- 模型訓練的核心特徵欄位，都已獨立出來
    recorded_at TIMESTAMPTZ NOT NULL,               -- 時間序列特徵：天氣數據記錄的時間
    temperature_celsius NUMERIC(4, 1) NOT NULL,     -- 數值特徵：溫度 (攝氏度)
    humidity_percent SMALLINT NOT NULL CHECK (humidity_percent >= 0 AND humidity_percent <= 100), -- 數值特徵：相對濕度
    precipitation_mm NUMERIC(6, 2) NOT NULL,        -- 數值特徵：累積降雨量
    
    -- 非核心，但仍有價值的欄位
    source VARCHAR(50) NOT NULL,                    -- 數據來源 (e.g., 'CWB', 'OpenWeatherMap')
    weather_metadata JSONB                          -- 用於存放額外的非結構化元資料，如風速、風向、感測器ID等
);

---
--- 建立索引以優化查詢效能
---

-- 標準 B-tree 索引 (適用於外鍵查詢和等值/範圍查詢)
CREATE INDEX idx_paths_poi_trail_id ON paths.points_of_interest(trail_id);
CREATE INDEX idx_user_gpx_uploads_user_id ON user_gpx.gpx_uploads(user_id);
CREATE INDEX idx_user_gpx_uploads_trail_id ON user_gpx.gpx_uploads(trail_id);
CREATE INDEX idx_user_gpx_gpx_track_points_upload_id ON user_gpx.gpx_track_points(gpx_upload_id);
CREATE INDEX idx_weather_readings_station_id ON weather.readings(station_id);
CREATE INDEX idx_weather_readings_recorded_at ON weather.readings(recorded_at);

-- 建立 PostGIS 空間索引 (GIST Index)
-- GIST 索引對於空間查詢 (例如：查找特定區域內的點/線) 至關重要
CREATE INDEX idx_paths_trails_route_geometry ON paths.trails USING GIST (route_geometry);
CREATE INDEX idx_paths_poi_location ON paths.points_of_interest USING GIST (location);
CREATE INDEX idx_user_gpx_gpx_track_points_location ON user_gpx.gpx_track_points USING GIST (location);
CREATE INDEX idx_weather_readings_location ON weather.readings USING GIST (location);
CREATE INDEX idx_user_gpx_gpx_uploads_route_geometry ON user_gpx.gpx_uploads USING GIST (gpx_route_geometry);
CREATE INDEX idx_weather_stations_location ON weather.stations USING GIST (location);

-- 建立 JSONB 索引 (GIN Index)
-- GIN 索引對於查詢 JSONB 內部鍵值對非常有效
CREATE INDEX idx_weather_data_gin ON weather.readings USING GIN (weather_data);
CREATE INDEX idx_weather_metadata_gin ON weather.readings USING GIN (weather_metadata);


---
--- 自動更新 updated_at 欄位的觸發器
---

-- 建立一個觸發器函數，用於在記錄更新時自動修改 updated_at 時間戳
CREATE OR REPLACE FUNCTION update_timestamp_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 應用觸發器到 paths.trails 資料表
CREATE TRIGGER update_paths_trails_timestamp
BEFORE UPDATE ON paths.trails
FOR EACH ROW
EXECUTE FUNCTION update_timestamp_column();

-- 應用觸發器到 paths.points_of_interest 資料表
CREATE TRIGGER update_paths_poi_timestamp
BEFORE UPDATE ON paths.points_of_interest
FOR EACH ROW
EXECUTE FUNCTION update_timestamp_column();

-- 觸發器 (假設您也想追蹤 weather.stations 的更新時間)
CREATE OR REPLACE FUNCTION update_timestamp_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_weather_stations_timestamp
BEFORE UPDATE ON weather.stations
FOR EACH ROW
EXECUTE FUNCTION update_timestamp_column();
