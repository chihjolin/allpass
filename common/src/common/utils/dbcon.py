# import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from .logger import get_logger

# ---------------------------------------------------
# Logging 設定（共用）
# ---------------------------------------------------
logger = get_logger(__name__)  # 使用自訂 logger


def make_engines(user, password, host, port, db, timezone="Asia/Taipei"):
    """
    建立同步 & 非同步 Engine，以及 Session 工廠
    回傳 tuple:(
        POSTGRES_URL,
        ASYNC_POSTGRES_URL,
        engine,
        async_engine,
        SessionLocal,
        AsyncSessionLocal,
    )
    """
    logger.info("開始設定資料庫連線: dbcon")
    # -------------------------
    # Connection URL
    # -------------------------
    POSTGRES_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    ASYNC_POSTGRES_URL = POSTGRES_URL.replace("psycopg2", "asyncpg")

    # -------------------------
    # Logging 印出 URL
    # -------------------------
    logger.info(f"SYNC_POSTGRES_URL: {POSTGRES_URL}")
    logger.info(f"ASYNC_POSTGRES_URL: {ASYNC_POSTGRES_URL}")

    # -------------------------
    # Engine 建立
    # -------------------------
    engine = create_engine(
        POSTGRES_URL,
        connect_args={"options": f"-c timezone={timezone}"},
        echo=False,
        future=True,
    )

    async_engine = create_async_engine(
        ASYNC_POSTGRES_URL,
        connect_args={"server_settings": {"timezone": timezone}},
        echo=False,
        future=True,
    )

    # # -------------------------
    # # Session 工廠
    # # -------------------------
    # SessionLocal = sessionmaker(
    #     bind=engine,
    #     autoflush=False,
    #     autocommit=False,
    # )
    # AsyncSessionLocal = async_sessionmaker(
    #     bind=async_engine,
    #     autoflush=False,
    #     autocommit=False,
    # )

    return (
        POSTGRES_URL,
        ASYNC_POSTGRES_URL,
        engine,
        async_engine,
        # SessionLocal,
        # AsyncSessionLocal,
    )


# ---------------------------------------------------
# 宣告 Base class，供 ORM model 繼承
# ---------------------------------------------------
class Base(DeclarativeBase):
    pass


# -------------------------
# FastAPI Dependency for SQLModel (sync)
# -------------------------
def get_session(engine):
    """
    FastAPI Dependency for SQLModel (sync)
    """

    def _get_session():
        with Session(engine) as session:
            yield session

    return _get_session


# -------------------------
# FastAPI Dependency for SQLModel (async)
# -------------------------
def get_async_session(async_engine):
    """
    FastAPI Dependency for SQLModel (async)
    """

    async def _get_async_session():
        # expire_on_commit=False 對於 async 來說很重要，避免存取屬性時觸發隱式 IO
        async with AsyncSession(async_engine, expire_on_commit=False) as session:
            yield session

    return _get_async_session
