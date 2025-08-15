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
    id SERIAL PRIMARY KEY,                          -- serial id 自動遞增
    trail_name_ch VARCHAR(100),                     -- 路徑中文名
    trail_name_en VARCHAR(100) NOT NULL UNIQUE,     -- 路徑英文名, 必須有值且非空字串
    location_name VARCHAR(50),                      -- 路徑地點                
    -- difficulty SMALLINT,                         -- 路徑難度 (例如 1-5 等級)
    permit_required boolean NOT NULL DEFAULT false, -- 是否需要入山證
    length_km NUMERIC(6, 2),                        -- 路徑總長度 (公里)，保留兩位小數
    elevation_start_m INT,                          -- 起始高度（公尺）
    elevation_end_m INT,                            -- 頂點高度 (公尺)
    -- elevation_gain_m INT,                        -- 總爬升高度 (公尺)
    -- descent_m INT,                               -- 總下降（公尺）
    -- estimated_duration_h NUMERIC(5, 2),          -- 估計完成時間 (小時)，保留兩位小數
    -- weather_station VARCHAR(100),                --氣象站位置
    route_geometry GEOMETRY(LineString, 4326),      -- 路徑的地理幾何形狀，使用 LineString 類型和 WGS84 座標系 (EPSG:4326)
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 記錄建立時間，預設為當前時間帶時區
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄更新時間，預設為當前時間帶時區
);

-- paths.points_of_interest: 儲存路徑上的興趣點 (POI)
CREATE TABLE paths.points_of_interest (
    id SERIAL PRIMARY KEY,                          -- 唯一識別碼
    poi_name VARCHAR(100) NOT NULL,                 -- 興趣點名稱
    poi_type VARCHAR(50),                           -- 興趣點類型 (例如：登山口, 岔路, 營地, 水源),
    -- location_twd97 GEOMETRY(Point, 3826)         -- 興趣點的地理位置，使用 Point 類型和 TWD97（台灣大地基準 1997）座標
    geolocation GEOMETRY(Point, 4326) NOT NULL,     -- 興趣點的地理位置，使用 Point 類型和 WGS84 座標系
    description TEXT,                               -- 興趣點的詳細描述
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 記錄建立時間
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄更新時間，預設為當前時間帶時區            
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
    trail_id INT REFERENCES paths.trails(id),
    segment_name VARCHAR(255),                      -- 使用者為此路徑段提供的名稱
    record_date DATE NOT NULL,                      -- GPX 記錄的日期 (從 GPX 內部時間戳提取)
    start_at TIMESTAMPTZ NOT NULL,                -- GPX 記錄的開始時間點 (帶時區)
    end_at TIMESTAMPTZ NOT NULL,                  -- GPX 記錄的結束時間點 (帶時區)
    avg_speed_km_h NUMERIC(5, 2),                    -- GPX 軌跡的平均速度 (公里/小時)
    accumulate_time INT,                            -- GPX 軌跡的總持續時間 (秒)
    total_distance_m NUMERIC(10, 2),                -- GPX 軌跡的總距離 (公尺)
    processing_status VARCHAR(20) DEFAULT 'pending', -- GPX 檔案的處理狀態 (e.g., 'pending', 'processed', 'failed')
    notes TEXT,                                     -- 使用者或其他額外筆記
    gpx_route_geometry GEOMETRY(LineString, 4326),  -- 將使用者軌跡存為 LineString，方便空間查詢
    uploaded_at TIMESTAMPTZ DEFAULT NOW()           -- 檔案上傳到系統的時間
);

-- user_gpx.gpx_track_points: 儲存 GPX 軌跡中的每一個點的詳細資訊
CREATE TABLE user_gpx.gpx_track_points (
    id BIGSERIAL PRIMARY KEY,                       -- 唯一識別碼
    gpx_upload_id BIGINT NOT NULL REFERENCES user_gpx.gpx_uploads(id) ON DELETE CASCADE, -- 外鍵，關聯到 user_gpx.gpx_uploads 表
    geolocation GEOMETRY(PointZ, 4326) NOT NULL,       -- 軌跡點的地理位置 (包含經度、緯度和高程 Z)，使用 WGS84 座標系
    recorded_at TIMESTAMPTZ NOT NULL                -- 軌跡點記錄的時間 (帶時區)
);

-------------------------------------
-- Schema: weather (天氣資料)
-------------------------------------
-- weather.stations: 儲存天氣站
CREATE TABLE weather.stations (
    id SERIAL PRIMARY KEY,                          -- 天氣站的唯一識別碼
    station_code VARCHAR(100) NOT NULL UNIQUE,      -- 天氣站站號，必須唯一
    station_name VARCHAR(100),                      -- 天氣站名稱
    geolocation GEOMETRY(Point, 4326) NOT NULL,     -- 天氣站的地理位置
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

-------------------------------------
-- 建立關聯表
-------------------------------------

-- paths.trail_pois: 路徑與興趣點 (POI)的關聯
CREATE TABLE paths.trail_pois(
    id SERIAL PRIMARY KEY,                          -- 唯一識別碼
    trail_id INT REFERENCES paths.trails(id) ON DELETE CASCADE, -- 外鍵，關聯到 paths.trails 表，如果路徑被刪除，相關關聯也會被刪除
    poi_id INT REFERENCES paths.points_of_interest(id) ON DELETE CASCADE, -- 外鍵，關聯到 paths.points_of_interest 表，如果POI被刪除，相關關聯也會被刪除
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 記錄建立時間
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄更新時間，預設為當前時間帶時區            
);

-- paths.trail_station: 路徑與氣象站的關聯 
CREATE TABLE paths.trail_stations(
    id SERIAL PRIMARY KEY,                          -- 唯一識別碼
    trail_id INT REFERENCES paths.trails(id) ON DELETE CASCADE, -- 外鍵，關聯到 paths.trails 表，如果路徑被刪除，相關關聯也會被刪除
    station_id INT REFERENCES weather.stations(id) ON DELETE CASCADE, -- 外鍵，關聯到 weather.stations 表，如果氣象站被刪除，相關關聯也會被刪除
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 記錄建立時間
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 記錄更新時間，預設為當前時間帶時區            
);


-------------------------------------
--- 建立索引以優化查詢效能
-------------------------------------

-- 標準 B-tree 索引 (適用於外鍵查詢和等值/範圍查詢)
-- CREATE INDEX idx_paths_poi_trail_id ON paths.points_of_interest(trail_id);
CREATE INDEX idx_user_gpx_uploads_user_id ON user_gpx.gpx_uploads(user_id);
CREATE INDEX idx_user_gpx_uploads_trail_id ON user_gpx.gpx_uploads(trail_id);
CREATE INDEX idx_gpx_track_points_upload_time ON user_gpx.gpx_track_points(gpx_upload_id, recorded_at);
CREATE INDEX idx_weather_readings_station_time ON weather.readings(station_id, recorded_at);

-- 建立 PostGIS 空間索引 (GIST Index)
-- GIST 索引對於空間查詢 (例如：查找特定區域內的點/線) 至關重要
CREATE INDEX idx_paths_trails_route_geometry ON paths.trails USING GIST (route_geometry);
CREATE INDEX idx_paths_poi_location ON paths.points_of_interest USING GIST (geolocation);
CREATE INDEX idx_user_track_points_location ON user_gpx.gpx_track_points USING GIST (geolocation);
CREATE INDEX idx_user_uploads_route_geometry ON user_gpx.gpx_uploads USING GIST (gpx_route_geometry);
CREATE INDEX idx_weather_stations_location ON weather.stations USING GIST (geolocation);

-- 建立 JSONB 索引 (GIN Index)
-- GIN 索引對於查詢 JSONB 內部鍵值對非常有效
CREATE INDEX idx_weather_metadata_gin ON weather.readings USING GIN (weather_metadata);

-------------------------------------
--- 建立一個自動更新 created_at & updated_at 欄位的觸發器
-------------------------------------
-- 刪除舊的 function（若存在）
DROP FUNCTION IF EXISTS set_created_updated_timestamp() CASCADE;

-- 建立 function：自動設定 created_at & updated_at
CREATE OR REPLACE FUNCTION set_created_updated_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.created_at = COALESCE(NEW.created_at, NOW());
        NEW.updated_at = NOW();
    ELSIF TG_OP = 'UPDATE' THEN
        NEW.updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 自動偵測指定 schema 下所有有 created_at & updated_at 的 table，掛上觸發器
DO $$
DECLARE
    r RECORD;
    trig_name TEXT;
BEGIN
    FOR r IN
        SELECT table_schema, table_name
        FROM information_schema.columns
        WHERE column_name IN ('created_at','updated_at')
          AND table_schema IN ('paths','user_gpx','weather')
        GROUP BY table_schema, table_name
        HAVING COUNT(DISTINCT column_name) = 2  -- 只選有 created_at + updated_at 的 table
    LOOP
        -- 生成 trigger 名稱
        trig_name := 'trg_update_' || r.table_schema || '_' || r.table_name;

        -- 先刪掉舊的 trigger（如果存在）
        EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I.%I', trig_name, r.table_schema, r.table_name);

        -- 建立新的 trigger
        EXECUTE format(
            'CREATE TRIGGER %I
             BEFORE INSERT OR UPDATE ON %I.%I
             FOR EACH ROW
             EXECUTE FUNCTION set_created_updated_timestamp()',
            trig_name, r.table_schema, r.table_name
        );
    END LOOP;
END $$;


-- -- 應用觸發器到 paths.trails 資料表
-- CREATE TRIGGER update_paths_trails_timestamp
-- BEFORE UPDATE ON paths.trails
-- FOR EACH ROW EXECUTE FUNCTION update_timestamp_column();

-- -- 應用觸發器到 paths.points_of_interest 資料表
-- CREATE TRIGGER update_paths_poi_timestamp
-- BEFORE UPDATE ON paths.points_of_interest
-- FOR EACH ROW EXECUTE FUNCTION update_timestamp_column();

-- -- 應用觸發器到 weather.stations 資料表
-- CREATE TRIGGER update_weather_stations_timestamp
-- BEFORE UPDATE ON weather.stations
-- FOR EACH ROW EXECUTE FUNCTION update_timestamp_column();

-- 插入範例資料paths.trails
-- INSERT INTO paths.trails (trail_id, name, baiyue_peak_name, location, difficulty, permit_required, length_km, elevation_gain_m, descent_m, estimated_duration_h, weather_station) VALUES
-- ('hehuan-main','合歡南峰', '合歡山','南投縣仁愛鄉', 1, false, 3.6, 150, 150, 1.5, '仁愛鄉'),
-- ('hehuan-north','合歡北峰', '合歡山','南投縣仁愛鄉', 3, false, 4.7, 450, 450, 4, '仁愛鄉'),
-- ('yangmingshan-east','陽明山東段縱走', '陽明山','臺北市士林區', 5, false, 12, 800, 750, 6, '士林區'),
-- ('taoshan-waterfall','桃山瀑布', '桃山','臺中市和平區', 2, true, 8.6, 400, 400, 3, '和平區'),
-- ('mountjade','玉山主峰', '玉山','嘉義縣阿里山鄉', 5, true, 20, 3952, 3800, 3, '阿里山鄉');