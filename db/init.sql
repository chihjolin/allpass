-- 啟用 PostGIS 擴充套件
-- PostGIS 提供豐富的空間資料類型和函數，是處理地理資訊的核心
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
    baiyue_name VARCHAR(50),                        -- 百岳名稱
    name VARCHAR(100) NOT NULL UNIQUE,              -- 路徑名稱，必須唯一
    difficulty SMALLINT,                            -- 難度等級，方便篩選
    distance_km NUMERIC(6, 2),                      -- 路徑總長度 (公里)，保留兩位小數
    total_ascent_m INT,                             -- 總爬升高度 (公尺) 
    total_descent_m INT,                            -- 總下降高度 (公尺) 
    total_time_h NUMERIC(5, 2),                     -- 估計完成時間 (小時)，保留兩位小數
    route_geometry GEOMETRY(LineString, 4326),      -- 路徑的地理幾何形狀
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 記錄建立時間
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄更新時間
);

-- paths.points_of_interest: 儲存路徑上的觀測點/興趣點 (POI)
-- 觀測點的類型 (poi_type) 可以是 '登山口', '營地', '山頂', '水源', '通訊點' 等
CREATE TABLE paths.points_of_interest (
    id SERIAL PRIMARY KEY,                          -- 唯一識別碼
    trail_id INT REFERENCES paths.trails(id) ON DELETE CASCADE, -- 外鍵，關聯到 paths.trails 表
    name VARCHAR(100) NOT NULL,                     -- 觀測點名稱
    poi_type VARCHAR(50),                           -- 觀測點類型 (e.g., '山頂', '登山口', '通訊點')
    location GEOMETRY(Point, 4326) NOT NULL,        -- 觀測點的地理位置
    description TEXT,                               -- 詳細描述
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 記錄建立時間
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄更新時間
);

-------------------------------------
-- Schema: user_gpx (使用者上傳的資料)
-------------------------------------
-- user_gpx.users: 儲存使用者基本資訊
CREATE TABLE user_gpx.users (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼
    username VARCHAR(50) UNIQUE NOT NULL,           -- 使用者名稱
    created_at TIMESTAMPTZ DEFAULT NOW()            -- 帳戶建立時間
);

-- user_gpx.gpx_uploads: 儲存使用者上傳的 GPX 檔案的摘要資訊
CREATE TABLE user_gpx.gpx_uploads (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼
    user_id BIGINT NOT NULL REFERENCES user_gpx.users(id) ON DELETE CASCADE, -- 外鍵
    trail_id INT REFERENCES paths.trails(id),       -- 關聯到 paths.trails，允許為 NULL
    file_name VARCHAR(255) NOT NULL,                -- 原始 GPX 檔案名稱
    segment_name VARCHAR(255),                      -- 使用者為此路徑段提供的名稱
    total_distance_m NUMERIC(10, 2),                -- 總距離 (公尺) (優化：重新加入)
    total_duration_s INT,                           -- 總持續時間 (秒) (優化：重新加入)
    avg_speed_kmh NUMERIC(5, 2),                    -- 平均速度 (公里/小時) (優化：重新加入)
    start_time TIMESTAMPTZ,                         -- 軌跡開始時間 (優化：重新加入)
    end_time TIMESTAMPTZ,                           -- 軌跡結束時間 (優化：重新加入)
    processing_status VARCHAR(20) DEFAULT 'pending', -- GPX 檔案的處理狀態
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),          -- 檔案上傳到系統的時間
    gpx_route_geometry GEOMETRY(LineString, 4326)   -- 軌跡的幾何形狀 (優化：新增欄位)
);

-- user_gpx.gpx_track_points: 儲存 GPX 軌跡中的每一個點的詳細資訊
CREATE TABLE user_gpx.gpx_track_points (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼
    gpx_upload_id BIGINT NOT NULL REFERENCES user_gpx.gpx_uploads(id) ON DELETE CASCADE, -- 外鍵
    location GEOMETRY(PointZ, 4326) NOT NULL,       -- 軌跡點的地理位置 (經度、緯度、高程)
    recorded_at TIMESTAMPTZ NOT NULL                -- 軌跡點記錄的時間 (優化：避免關鍵字)
);

-------------------------------------
-- Schema: weather (天氣資料)
-------------------------------------
-- weather.readings: 儲存各個地點和時間的天氣觀測數據
CREATE TABLE weather.readings (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼
    poi_id INT REFERENCES paths.points_of_interest(id), -- 外鍵
    location GEOMETRY(Point, 4326) NOT NULL,        -- 天氣觀測地點的地理位置
    recorded_at TIMESTAMPTZ NOT NULL,               -- 天氣數據記錄的時間 (優化：避免關鍵字)
    weather_data JSONB NOT NULL,                    -- 天氣的詳細數據
    source VARCHAR(50)                              -- 天氣數據的來源
);

---
--- 建立索引以優化查詢效能
---

-- 標準 B-tree 索引
CREATE INDEX idx_paths_poi_trail_id ON paths.points_of_interest(trail_id);
CREATE INDEX idx_user_gpx_uploads_user_id ON user_gpx.gpx_uploads(user_id);
CREATE INDEX idx_user_gpx_uploads_trail_id ON user_gpx.gpx_uploads(trail_id);
CREATE INDEX idx_user_gpx_gpx_track_points_upload_id ON user_gpx.gpx_track_points(gpx_upload_id);
CREATE INDEX idx_weather_readings_poi_id ON weather.readings(poi_id);

-- 建立 PostGIS 空間索引 (GIST Index)
CREATE INDEX idx_paths_trails_route_geometry ON paths.trails USING GIST (route_geometry);
CREATE INDEX idx_paths_poi_location ON paths.points_of_interest USING GIST (location);
CREATE INDEX idx_user_gpx_gpx_track_points_location ON user_gpx.gpx_track_points USING GIST (location);
CREATE INDEX idx_weather_readings_location ON weather.readings USING GIST (location);
CREATE INDEX idx_user_gpx_gpx_uploads_route_geometry ON user_gpx.gpx_uploads USING GIST (gpx_route_geometry); -- 優化：新增索引

-- 建立 JSONB 索引 (GIN Index)
CREATE INDEX idx_weather_data_gin ON weather.readings USING GIN (weather_data);

-- 自動更新 updated_at 欄位的觸發器
-- 適用於所有需要追蹤更新時間的表格
CREATE OR REPLACE FUNCTION update_timestamp_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_paths_trails_timestamp
BEFORE UPDATE ON paths.trails
FOR EACH ROW
EXECUTE FUNCTION update_timestamp_column();

CREATE TRIGGER update_paths_poi_timestamp
BEFORE UPDATE ON paths.points_of_interest
FOR EACH ROW
EXECUTE FUNCTION update_timestamp_column();
