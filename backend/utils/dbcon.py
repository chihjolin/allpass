import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

# 讀取 .env 設定
load_dotenv(override=True)
#load_dotenv()

# 組合連線字串
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print("DB_URL:", DATABASE_URL)


# 建立 Engine 和 Session
engine = create_engine(DATABASE_URL, echo=False, future=True)

# 可多執行緒使用的 ScopedSession
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

# 宣告 Base class，讓模型繼承
Base = declarative_base()