import logging

# from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from .logger import get_logger

# import os
# from pathlib import Path


# from backendf.core.env import settings  # 或其他 config module


# ---------------------------------------------------
# Logging 設定（共用）
# ---------------------------------------------------
logger = get_logger(name=__name__, level=logging.INFO)  # 使用自訂 logger
logger.info("開始設定資料庫連線: dbcon")


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


# # -------------------------
# # # 這是 Dependency: connection context manager (SQLAlchemy Core)
# # # Legacy / SQLAlchemy (DO NOT USE FOR NEW API)
# # -------------------------
# def get_conn():
#     with engine.begin() as conn:  # 自動開啟 Transaction
#         yield conn  # 將連線交給 API Function
#         # 函數結束後自動 Commit 或 Rollback


# # ---------------------------------------------------
# # Session 工廠(未來適用純 SQLAlchemy model)
# # ---------------------------------------------------

# # 適用於多執行緒（Flask context）
# SessionLocal = sessionmaker(
#     bind=engine,
#     autoflush=False,
#     autocommit=False,
# )


# # FastAPI 用 async session
# AsyncSessionLocal = async_sessionmaker(
#     bind=async_engine,
#     autoflush=False,
#     autocommit=False,
# )


# ---------------------------------------------------
# 宣告 Base class，供 ORM model 繼承
# ---------------------------------------------------
class Base(DeclarativeBase):
    pass


# -------------------------
# FastAPI Dependency for SQLModel (sync)
# -------------------------
# def get_session(engine):
#     """
#     FastAPI Dependency for SQLModel (sync).

#     使用時機：
#     - FastAPI sync endpoint (def)
#     - SQLModel ORM 操作
#     - 現階段專案主線
#     """
#     with Session(engine) as session:
#         yield session


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
# async def get_async_session():
#     """
#     FastAPI Dependency for SQLModel (async).

#     使用時機：
#     - FastAPI async endpoint (async def)
#     - 高併發 I/O
#     - 下一單元 AsyncIO
#     """
#     async with AsyncSession(async_engine) as session:
#         yield session


def get_async_session(async_engine):
    """
    FastAPI Dependency for SQLModel (async)
    """

    async def _get_async_session():
        # expire_on_commit=False 對於 async 來說很重要，避免存取屬性時觸發隱式 IO
        async with AsyncSession(async_engine, expire_on_commit=False) as session:
            yield session

    return _get_async_session
