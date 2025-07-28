分支 (`feature/database-setup`) 用於建立基礎 PostgreSQL 架構，並包含空間資料處理能力 (PostGIS)，以便處理與登山路線、使用者 GPX 上傳和天氣資料相關的地理資訊。

**綱要 (Schema) 組織：** 暫定～～

- `paths`: 儲存官方或策展的登山路徑資料。
- `user_gpx`: 管理使用者上傳的 GPX 軌跡資訊。
- `weather`: 包含天氣觀測數據，可能與特定的地理位置或興趣點相關聯。

## 入門指南 (資料庫設定)

要從此分支設定並運行資料庫，請遵循以下步驟：

1. **複製專案倉庫切換到功能分支：**git clone 完 cd allpass
2. **確保 Docker 正在運行：** 確保您的系統上已啟動 Docker Desktop
3. **審閱資料庫初始化腳本：**
    
    位於 `./database/init.sql` 的 `init.sql` 腳本包含所有用於建立綱要、資料表、索引和觸發器的 SQL 命令。當 `postgis/postgis` 容器首次啟動時，此腳本會透過 `docker-compose.yml` 中的 `volumes: - ./db:/docker-entrypoint-initdb.d` 映射自動執行。
    
4. **設定資料庫密碼 ：**
    
    開啟 `docker-compose.yml`。為了安全考量，強烈建議將 `POSTGRES_PASSWORD` 從 `allpass` 更改為一個強大且獨特的密碼。
    
    ```yaml
    # ...
    
    environment:
    
      POSTGRES_DB: allpass_db
    
      POSTGRES_USER: allpass_user
    
      POSTGRES_PASSWORD: 您的_強密碼_在此處 # <--- 請務必更改！
    
    # ...
    
    ```
    
5. **啟動資料庫容器：**
    
    在終端機中，導航到已複製的倉庫根目錄 (即 `docker-compose.yml` 所在的位置)，
    然後執行：
    
    ```bash
    docker-compose up -d
    ```
    
    此命令將會：
    
    - 如果本機沒有 `postgis/postgis:16-3.4` Docker 映像檔，則會下載它。
    - 建立並啟動一個名為 `allpass_postgres` 的容器。
    - 將容器的 `5432` 埠映射到您的主機。
    - 將 `./db` 目錄 (包含 `init.sql`) 掛載到容器的初始化目錄中，使得 `init.sql` 在首次啟動時運行。
    - 將資料庫數據持久化到名為 `postgres_data` 的 Docker Volume 中。
6. **驗證容器狀態：**
    
    您可以使用 Docker Desktop 或執行以下命令來檢查容器狀態和埠映射：
    
    ```bash
    docker ps
    ```
    
    您應該會看到 `allpass_postgres` 容器的 `PORTS` 欄位顯示類似 `0.0.0.0:5432->5432/tcp` 的資訊。
