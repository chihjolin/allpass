import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

# 讀取 .env 設定
load_dotenv()

# 宣告 Base class，讓模型繼承
Base = declarative_base()

class PostgresDB:
    def __init__(self, env_prefix="DB"):
        self.env_prefix = env_prefix
        self.session = None
        self.engine = None

    def connect(self):
        user = os.getenv(f"{self.env_prefix}_USER")
        password = os.getenv(f"{self.env_prefix}_PASSWORD")
        host = os.getenv(f"{self.env_prefix}_HOST")
        port = os.getenv(f"{self.env_prefix}_PORT")
        db = os.getenv(f"{self.env_prefix}_NAME")
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
        # 建立 Engine 和 Session
        self.engine = create_engine(url, echo=False, future=True)
        # 可多執行緒使用的 ScopedSession
        self.session = scoped_session(sessionmaker(bind=self.engine, autoflush=False, autocommit=False))

    def get_session(self):
        return self.session()