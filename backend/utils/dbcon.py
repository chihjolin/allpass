import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

# # 讀取 .env 設定(僅開發測試用)
# load_dotenv(override=True)


# 組合連線字串
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


POSTGRES_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
print("POSTGRES_URL:", POSTGRES_URL)


# 建立 Engine 和 Session
engine = create_engine(POSTGRES_URL, echo=False, future=True)

# 可多執行緒使用的 ScopedSession
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

# 宣告 Base class，讓模型繼承
Base = declarative_base()