-- 啟用 PostGIS 擴充套件
-- PostGIS 提供空間資料類型和函數，是處理地理資訊的核心
CREATE EXTENSION IF NOT EXISTS postgis;

-- 建立三個核心 Schemas (資料庫模式/命名空間)
-- Schemas 有助於組織資料表，避免命名衝突，並提高資料庫管理效率
CREATE SCHEMA IF NOT EXISTS paths;      -- 存放官方/預定義的路徑資料
CREATE SCHEMA IF NOT EXISTS user_gpx;   -- 存放使用者上傳的 GPX 軌跡資料
CREATE SCHEMA IF NOT EXISTS weather;    -- 存放天氣相關的觀測資料

-------------------------------------
--- Schema: paths (官方路徑資料)
-------------------------------------
-- paths.trails: 儲存詳細的官方路徑資訊
CREATE TABLE paths.trails (
    --id SERIAL,                                      -- serial id 自動遞增
    trail_id VARCHAR(100) PRIMARY KEY,              -- 路徑id, 唯一識別碼
    name VARCHAR(100) NOT NULL UNIQUE,              -- 路徑名稱，必須唯一
    baiyue_peak_name VARCHAR(50),                   -- 如果是百岳路徑，可填寫百岳名稱
    location VARCHAR(50),                           -- 路徑地點                
    difficulty SMALLINT,                            -- 路徑難度 (例如 1-5 等級)
    permit_required boolean,                         -- 是否需要入山證
    length_km NUMERIC(6, 2),                        -- 路徑總長度 (公里)，保留兩位小數
    elevation_gain_m INT,                           -- 總爬升高度 (公尺)
    descent_m INT,                                  -- 總下降（公尺）
    estimated_duration_h NUMERIC(5, 2),             -- 估計完成時間 (小時)，保留兩位小數
    weather_station VARCHAR(100),                    --氣象站位置
    route_geometry GEOMETRY(LineString, 4326),      -- 路徑的地理幾何形狀，使用 LineString 類型和 WGS84 座標系 (EPSG:4326)
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 記錄建立時間，預設為當前時間帶時區
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄更新時間，預設為當前時間帶時區
);

-- paths.points_of_interest: 儲存路徑上的興趣點 (POI)
CREATE TABLE paths.points_of_interest (
    id SERIAL PRIMARY KEY,                          -- 唯一識別碼
    trail_id VARCHAR(100) REFERENCES paths.trails(trail_id) ON DELETE CASCADE, -- 外鍵，關聯到 paths.trails 表，如果路徑被刪除，相關 POI 也會被刪除
    --trail_id INT REFERENCES paths.trails(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,                     -- 興趣點名稱
    poi_type VARCHAR(50),                           -- 興趣點類型 (例如：登山口, 岔路, 營地, 水源)
    location GEOMETRY(Point, 4326) NOT NULL,        -- 興趣點的地理位置，使用 Point 類型和 WGS84 座標系
    description TEXT,                               -- 興趣點的詳細描述
    created_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄建立時間
);

-------------------------------------
--- Schema: user_gpx (使用者上傳的資料)
-------------------------------------
-- user_gpx.users: 儲存使用者基本資訊
CREATE TABLE user_gpx.users (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼，使用 BIGSERIAL 避免 ID 不足
    username VARCHAR(50) UNIQUE NOT NULL,           -- 使用者名稱，必須唯一且非空
    created_at TIMESTAMPTZ DEFAULT NOW()            -- 帳戶建立時間
);

-- user_gpx.gpx_uploads: 儲存使用者上傳的 GPX 檔案的摘要資訊
-- 包含您要求修改後的欄位，並針對 JOIN 做了優化
CREATE TABLE user_gpx.gpx_uploads (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼
    user_id BIGINT NOT NULL REFERENCES user_gpx.users(id) ON DELETE CASCADE, -- 外鍵，關聯到 user_gpx.users 表，使用者被刪除時其上傳記錄也刪除
    file_name VARCHAR(255) NOT NULL,                -- 原始 GPX 檔案名稱
    -- trail_id: 關聯到 paths.trails，表示此 GPX 可能屬於哪條官方路徑
    -- 允許 NULL，因為使用者上傳的路徑可能不匹配任何官方路徑
    trail_id VARCHAR(100) REFERENCES paths.trails(trail_id),
    --trail_id INT REFERENCES paths.trails(id),
    segment_name VARCHAR(255),                      -- 使用者為此路徑段提供的名稱
    record_date DATE NOT NULL,                      -- GPX 記錄的日期 (從 GPX 內部時間戳提取)
    start_time TIMESTAMPTZ NOT NULL,                -- GPX 記錄的開始時間點 (帶時區)
    end_time TIMESTAMPTZ NOT NULL,                  -- GPX 記錄的結束時間點 (帶時區)
    avg_speed_kmh NUMERIC(5, 2),                    -- GPX 軌跡的平均速度 (公里/小時)
    accumulate_time INT,                            -- GPX 軌跡的總持續時間 (秒)
    total_distance_m NUMERIC(10, 2),                -- GPX 軌跡的總距離 (公尺)
    processing_status VARCHAR(20) DEFAULT 'pending', -- GPX 檔案的處理狀態 (e.g., 'pending', 'processed', 'failed')
    notes TEXT,                                     -- 使用者或其他額外筆記
    uploaded_at TIMESTAMPTZ DEFAULT NOW()           -- 檔案上傳到系統的時間
);

-- user_gpx.gpx_track_points: 儲存 GPX 軌跡中的每一個點的詳細資訊
CREATE TABLE user_gpx.gpx_track_points (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼
    gpx_upload_id BIGINT NOT NULL REFERENCES user_gpx.gpx_uploads(id) ON DELETE CASCADE, -- 外鍵，關聯到 user_gpx.gpx_uploads 表
    location GEOMETRY(PointZ, 4326) NOT NULL,       -- 軌跡點的地理位置 (包含經度、緯度和高程 Z)，使用 WGS84 座標系
    recorded_at TIMESTAMPTZ NOT NULL                -- 軌跡點記錄的時間 (帶時區)
);

-------------------------------------
--- Schema: weather (天氣資料)
-------------------------------------
-- weather.readings: 儲存各個地點和時間的天氣觀測數據
CREATE TABLE weather.readings (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼
    -- poi_id: 關聯到 paths.points_of_interest，表示天氣數據是針對特定興趣點的
    -- 允許 NULL，因為天氣數據可能來自非 POI 的地點
    poi_id INT REFERENCES paths.points_of_interest(id),
    location GEOMETRY(Point, 4326) NOT NULL,        -- 天氣觀測地點的地理位置
    recorded_at TIMESTAMPTZ NOT NULL,               -- 天氣數據記錄的時間 (帶時區)
    weather_data JSONB NOT NULL,                    -- 天氣的詳細數據 (例如：溫度、濕度、降雨量、風速等)，使用 JSONB 儲存，方便擴展
    source VARCHAR(50)                              -- 天氣數據的來源 (e.g., 'CWB', 'OpenWeatherMap')
);

---
--- 建立索引以優化查詢效能
---

-- 標準 B-tree 索引 (適用於等值查詢和範圍查詢)
CREATE INDEX idx_poi_trail_id ON paths.points_of_interest(trail_id);
CREATE INDEX idx_gpx_uploads_user_id ON user_gpx.gpx_uploads(user_id);
CREATE INDEX idx_gpx_uploads_trail_id ON user_gpx.gpx_uploads(trail_id); -- gpx_uploads 與 trails 的 JOIN
CREATE INDEX idx_gpx_track_points_upload_id ON user_gpx.gpx_track_points(gpx_upload_id);
CREATE INDEX idx_weather_readings_poi_id ON weather.readings(poi_id);
CREATE INDEX idx_gpx_uploads_record_date ON user_gpx.gpx_uploads(record_date); -- 按日期查詢用戶上傳
CREATE INDEX idx_gpx_track_points_timestamp ON user_gpx.gpx_track_points(recorded_at); -- 按時間查詢軌跡點
CREATE INDEX idx_weather_readings_timestamp ON weather.readings(recorded_at); -- 按時間查詢天氣

-- 建立 PostGIS 空間索引 (GIST Index)
-- GIST 索引對於空間查詢 (例如：查找特定區域內的點/線) 至關重要
CREATE INDEX idx_trails_route_geometry ON paths.trails USING GIST (route_geometry);
CREATE INDEX idx_poi_location ON paths.points_of_interest USING GIST (location);
CREATE INDEX idx_gpx_track_points_location ON user_gpx.gpx_track_points USING GIST (location);
CREATE INDEX idx_weather_readings_location ON weather.readings USING GIST (location);

-- 建立 JSONB 索引 (GIN Index)
-- GIN 索引對於查詢 JSONB 內部鍵值對非常有效
CREATE INDEX idx_weather_data_gin ON weather.readings USING GIN (weather_data);

-- 自動更新 updated_at 欄位的觸發器 (可選，但推薦用於維護數據一致性)
-- 當 paths.trails 表的記錄被更新時，自動更新 updated_at 時間戳
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


-- 插入範例資料paths.trails
INSERT INTO paths.trails (trail_id, name, baiyue_peak_name, location, difficulty, permit_required, length_km, elevation_gain_m, descent_m, estimated_duration_h, weather_station) VALUES
('hehuan-main','合歡主峰', '合歡山','南投縣仁愛鄉', 1, false, 3.6, 150, 150, 1.5, '仁愛鄉'),
('hehuan-north','合歡北峰', '合歡山','南投縣仁愛鄉', 3, false, 4.7, 450, 450, 4, '仁愛鄉'),
('yangmingshan-east','陽明山東段縱走', '陽明山','臺北市士林區', 5, false, 12, 800, 750, 6, '士林區'),
('taoshan-waterfall','桃山瀑布', '桃山','臺中市和平區', 2, true, 8.6, 400, 400, 3, '和平區'),
('mountjade','玉山主峰', '玉山','嘉義縣阿里山鄉', 5, true, 20, 3952, 3800, 3, '阿里山鄉');