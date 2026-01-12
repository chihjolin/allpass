import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from .logger import get_logger

# ---------------------------------------------------
# Logging 設定（共用）
# ---------------------------------------------------
logger = get_logger(name=__name__, level=logging.INFO)  # 使用自訂 logger
logger.info("開始設定資料庫連線: dbcon")

# ---------------------------------------------------
# 讀取 .env 設定（僅本地開發用）
# load_dotenv() 只看 working directory，不看套件位置
# ---------------------------------------------------
load_dotenv(override=True)
print("dotenv loaded from:", os.getcwd())
# dotenv_path = Path(__file__).parent / ".env"
# load_dotenv(dotenv_path=dotenv_path, override=True)

# connection string
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


# -------------------------
# # 這是 Dependency: connection context manager (SQLAlchemy Core)
# # Legacy / SQLAlchemy (DO NOT USE FOR NEW API)
# -------------------------
def get_conn():
    with engine.begin() as conn:  # 自動開啟 Transaction
        yield conn  # 將連線交給 API Function
        # 函數結束後自動 Commit 或 Rollback


# ---------------------------------------------------
# Session 工廠(未來適用純 SQLAlchemy model)
# ---------------------------------------------------

# 適用於多執行緒（Flask context）
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# FastAPI 用 async session
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------
# 宣告 Base class，供 ORM model 繼承
# ---------------------------------------------------
class Base(DeclarativeBase):
    pass


# -------------------------
# FastAPI Dependency for SQLModel (sync)
# -------------------------
def get_session():
    """
    FastAPI Dependency for SQLModel (sync).

    使用時機：
    - FastAPI sync endpoint (def)
    - SQLModel ORM 操作
    - 現階段專案主線
    """
    with Session(engine) as session:
        yield session


# -------------------------
# FastAPI Dependency for SQLModel (async)
# -------------------------
async def get_async_session():
    """
    FastAPI Dependency for SQLModel (async).

    使用時機：
    - FastAPI async endpoint (async def)
    - 高併發 I/O
    - 下一單元 AsyncIO
    """
    async with AsyncSession(async_engine) as async_session:
        yield async_session
