import os
from dotenv import load_dotenv

# 從專案根目錄載入 .env 檔案
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Google Gemini API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# PostgreSQL Database URI
DB_USER = os.getenv("POSTGRES_USER", "allpass_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "allpass")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "allpass_db")

DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
