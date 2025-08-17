feature/report-generation 這個分支的核心目標，是利用大型語言模型（LLM）的強大能力，將單純的 GPX 軌跡數據轉化為富有見解、充滿鼓勵，且易於閱讀的個人化行程報告。

## ✨ 功能亮點
智能報告生成: 透過 LangChain 串聯 Google Gemini 模型，根據使用者上傳的 GPX 數據自動生成報告。

數據驅動的洞察: 報告不僅包含基本行程資訊，更提供速度分析、官方時長對比等深度見解。

鼓勵性語氣: 採用專業且正面的「AllPass 小助手」角色，讓報告讀起來更溫暖、更有動力。

## ⚙️ 技術棧
LLM 核心: Google Gemini 1.5 Flash

編程語言: Python 3.13

LLM 框架: LangChain

快取與非同步: Redis

容器化: Docker & Docker Compose

## 🏗️ 專案架構
此專案採用了簡化的微服務架構，旨在處理 LLM API 呼叫的成本與延遲問題：

report_generator.py: 核心邏輯腳本，負責從模擬數據源獲取行程資料，並調用 LLM 生成報告。

config.py: 存放 API 金鑰等敏感資訊，與程式碼分離，便於管理。

## 🚀 快速上手
前置作業
請確保您的開發環境已安裝：
Docker
Python 3.13

設定步驟
複製專案:
```bash
git clone https://github.com/chihjolin/allpass.git
cd allpass
git checkout feature/report-generation
```
配置 API 金鑰:
從 config_example.py 複製一份設定檔，並命名為 config.py。
```bash
cp config_example.py config.py
```
打開 config.py，填入您的 Google AI Studio API 金鑰。

GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"

安裝 Python 依賴:
```bash
pip install -r requirements.txt
```
執行專案
啟動 Redis 容器:
```bash
docker-compose up -d redis
```
此命令會啟動 Redis 服務，供你的 Python 腳本使用。

執行報告生成腳本:
```bash
python3 report_generator.py
```
腳本執行完成後，您將在終端機中看到一份客製化的登山報告。
