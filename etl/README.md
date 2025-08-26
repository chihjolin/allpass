# ETL 專案 README

## 專案簡介
ETL (Extract-Transform-Load) 專案負責：
- 從原始資料源抓取資料
- 執行資料清理與特徵計算
- 寫入 PostgreSQL 資料庫
- 支援可重用的 ETL job 管理

此專案已容器化，可搭配 Docker Compose 與其他服務整合。

---

## 專案架構

```plaintext
etl/
├── Dockerfile               # ETL 容器建置設定
├── __init__.py
├── init/
│   ├── __init__.py
│   ├── data/                # 初始化資料
│   └── init_postgres.py     # 初始化 PostgreSQL 資料表
├── jobs/
│   ├── __init__.py
│   ├── data/                # ETL job 使用的資料
│   ├── join_features.py     # 特徵計算 ETL job
│   └── runner.py            # 單一 job 執行程式
├── requirements.txt         # Python 相依套件
└── runner_entry.py          # ETL container 入口程式，管理初始化與 job 執行
```

## 功能說明

 - init/init_postgres.py
    - 建立資料庫與資料表
    - 只需執行一次，可用 flag 控制避免重複初始化

 - jobs/join_features.py
    - ETL job 範例：從 raw table 計算特徵，存入 feature table

- jobs/runner.py
    - 封裝單一 job 的執行函式，方便在 container 或測試中呼叫

- runner_entry.py
    - 容器啟動入口
    - 依序：
        - 初始化資料庫 (init_postgres)
        - 執行指定 ETL job
        - 可透過 flag 控制 job 是否執行，避免重複處理

##　使用方式
1. 安裝相依套件
```
pip install -r requirements.txt
```

2. 本地測試 ETL job
```
python jobs/runner.py  # 執行單一 job
```

3. 透過 container 執行 ETL
```
docker build -t etl_image .
docker run --env-file ../.env etl_image
````

 - 容器啟動時會先初始化資料表，再執行 runner_entry.py 管理的 ETL job。

## 注意事項

 - 初始化資料表

    - 建議使用 flag (INIT_FLAG) 控制只執行一次
    - 避免在每次 container 啟動時重建資料表，防止資料覆蓋

 - ETL job 可重複執行

    - 若有新資料進入，可重複呼叫 runner.py 或 container
    - 可依需求改寫 job 支援增量更新

 - 共用套件

    - 可與 common package 共用資料庫連線或工具函式
    - 避免在每個 job 重複建立 engine

- 容器熱更新

    - ETL 程式碼掛載 volume (- ./jobs:/app/jobs) 可支援開發模式熱更新

## 擴展建議

 - 新增更多 job，例如 calculate_statistics.py 或 clean_raw_data.py
 - 支援排程，例如用 cron 或 Airflow 定期觸發
 - 支援多資料源 ETL
 - 將 runner_entry 改寫為 CLI，方便指定要執行的 job