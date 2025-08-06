分支 (`feature/database-setup`) 用於建立基礎 PostgreSQL 架構，並包含空間資料處理能力 (PostGIS)，以便處理與登山路線、使用者 GPX 上傳和天氣資料相關的地理資訊。
使用 Docker 容器化技術，確保每位開發者的資料庫環境都是一致且獨立的，不會相互干擾。

## 核心理念

**「程式碼即環境」**：已將資料庫的配置 (`docker-compose.yml`) 和初始化腳本 (`init.sql`) 納入版本控制。
只要您的主機裝有 Docker，即可一鍵啟動一個完整且預載了初始資料的資料庫。

## 準備工作

在開始之前，請確保您的開發環境已安裝以下工具：

1.  **Git:** 用於複製專案程式碼。
2.  **Docker Desktop:** 用於執行資料庫容器。
3.  **DBeaver:** 一款強大的資料庫管理工具，方便您視覺化瀏覽與查詢資料。

## 步驟一：取得專案程式碼

首先，請透過 Git 複製專案，並切換到您要開發的分支。

```bash
# 複製專案倉庫
git clone [https://github.com/chihjolin/allpass.git](https://github.com/chihjolin/allpass.git)

# 進入專案目錄
cd allpass

# 切換到指定分支
git checkout feature/database-setup
```

## 步驟二：啟動本地資料庫
進入專案的根目錄後，只需一條命令即可啟動所有必要的服務。

```bash
# 啟動 PostgreSQL 容器，並在背景運行
docker-compose up -d
```

執行此命令後，Docker 將會：<br>
-自動下載 postgis/postgis:16-3.4 映像檔。<br>
-建立一個名為 allpass_postgres 的容器。<br>
-將容器的 5432 埠映射到您主機的 5423 埠。<br>
-自動執行 ./db/init.sql 腳本，建立所有資料表、索引，並載入初始資料。<br>

## 步驟三：驗證服務狀態
您可以使用以下命令確認容器是否已成功啟動。

```bash
docker ps
```
如果一切正常，您將在輸出中看到 allpass_postgres 容器，其 PORTS 欄位應顯示 0.0.0.0:5423->5432/tcp。


## 步驟四：連接資料庫並開始開發
現在，可以使用 DBeaver 或任何支援 PostgreSQL 的工具來連接資料庫。

```bash
連線設定：
主機 (Host): localhost
埠號 (Port): 5423
資料庫 (Database): allpass_db
使用者名稱 (Username): allpass_user
密碼 (Password): allpass (或您在 docker-compose.yml 中設定的密碼)
```

連線成功後，您就可以在 DBeaver 的「Database Navigator」中看到 paths、user_gpx、weather 等 Schema，並開始您的開發工作。

常見問題排解<br>
Q: 啟動時顯示「Port 5423 is already in use」？

A: 這表示您主機的 5423 埠已被其他程式佔用。您可以選擇：

停止佔用該埠的程式。

編輯 docker-compose.yml 檔案，將 ports 的主機埠號改為其他未使用的埠，例如 "5424:5432"，然後重新執行 docker-compose up -d。

Q: 重新啟動後資料庫是空的？

A: 這通常發生在您手動刪除了容器但未刪除資料 Volume。要強制 Docker 重新執行初始化腳本，請使用以下命令：

```bash
# 停止並刪除容器和 Volume (此操作會清除所有資料，請謹慎！)
docker-compose down -v

# 重新啟動
docker-compose up -d
```
