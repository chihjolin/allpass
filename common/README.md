# Common Package簡介

common 是一個 Python 共用工具套件，主要用於各個專案中共享通用功能，例如資料庫連線、工具函式等。
目前主要功能集中在 utils/dbcon.py，提供 PostgreSQL 的連線管理與 SQLAlchemy ORM 基礎建置。


## 專案結構  
```
common/
├── README.md
├── pyproject.toml        # PEP621 建構設定
└── src/
    └── common/
        ├── __init__.py
        ├── __pycache__/  # Python 自動產生快取
        └── utils/
            ├── __init__.py
            ├── __pycache__/
            └── dbcon.py  # 資料庫連線與 ORM 基礎設置
```


## 各目錄與檔案說明

- pyproject.toml
    - 定義此 package 的建構資訊，例如名稱、版本、依賴套件。
    - 支援使用 pip install . 安裝於專案環境中。

- src/common/init.py
    - 定義 common package 根模組，可讓 from common import ... 使用。

- src/common/utils/init.py
    - 工具函式的包裝目錄。
    - 目前包含 dbcon.py，未來可加入其他通用函式。

- src/common/utils/dbcon.py
    - 負責資料庫連線設定與 SQLAlchemy ORM 基礎建置。
    - 主要內容：
        - 讀取環境變數建立 PostgreSQL 連線字串
        - 建立 SQLAlchemy Engine、SessionLocal（可多執行緒使用）
        - 提供 Base 作為模型繼承基底

## 使用方式
1. 安裝 common package
```
cd common
pip install -e .
```

建議開發模式安裝 -e，可在修改原始碼後立即生效。

2. 在專案中使用
```
from common.utils.dbcon import engine, SessionLocal, Base
```

3. 設定環境變數

 - dbcon.py 會讀取以下環境變數（建議放在專案根目錄 .env）：
```
POSTGRES_HOST=localhost  
POSTGRES_PORT=5432  
POSTGRES_DB=mydb  
POSTGRES_USER=myuser  
POSTGRES_PASSWORD=mypassword 

```
可透過 python-dotenv 自動讀取 .env，目前在 dbcon.py 中已註解掉，可視專案需求打開。
 

## 未來擴展

新增更多通用工具函式，如資料清理、檔案管理、日誌工具等。

支援更多資料庫或第三方 API 共用連線管理。

提供開發、測試、正式環境切換功能。