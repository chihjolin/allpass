import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from .logger import get_logger

# ---------------------------------------------------
# Logging 設定（共用）
# ---------------------------------------------------
logger = get_logger(name=__name__, level=logging.INFO)  # 使用自訂 logger
logger.info("開始設定資料庫連線: dbcon")

# ---------------------------------------------------
# 讀取 .env 設定（僅本地開發用）
# ---------------------------------------------------
load_dotenv(override=True)
# dotenv_path = Path(__file__).parent / ".env"
# load_dotenv(dotenv_path=dotenv_path, override=True)


# 組合連線字串
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


POSTGRES_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
logger.info(f"POSTGRES_URL:{POSTGRES_URL}")
ASYNC_POSTGRES_URL = POSTGRES_URL.replace("postgresql+psycopg2", "postgresql+asyncpg")
logger.info(f"ASYNC_POSTGRES_URL: {ASYNC_POSTGRES_URL}")


# ---------------------------------------------------
# 同步版 Engine（給 legacy Flask、腳本使用）
# ---------------------------------------------------
engine = create_engine(
    POSTGRES_URL,
    connect_args={"options": "-c timezone=Asia/Taipei"},
    echo=False,
    future=True,
)

# ---------------------------------------------------
# 非同步版 Engine（給 FastAPI async def 使用）
# ---------------------------------------------------
async_engine = create_async_engine(
    ASYNC_POSTGRES_URL,
    connect_args={"server_settings": {"timezone": "Asia/Taipei"}},
    echo=False,
    future=True,
)

# ---------------------------------------------------
# Session 工廠
# ---------------------------------------------------

# 適用於多執行緒（Flask context）
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
)

# FastAPI 用 async session
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, autoflush=False, autocommit=False
)

# ---------------------------------------------------
# 宣告 Base class，供 ORM model 繼承
# ---------------------------------------------------
Base = declarative_base()
