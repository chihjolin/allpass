# import pytest_asyncio
import os

import pytest
from app.main import app  # type: ignore
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio.engine import AsyncEngine

# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from common.utils.dbcon import get_async_session, make_engines
from common.utils.logger import get_logger
from common.utils.logger_config import setup_logging

# from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------
# pytest 啟動時載入logging, .env.test設定
# ---------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def test_bootstrap():
    setup_logging()
    logger = get_logger(__name__)
    load_dotenv(".env.test")
    logger.info("Loaded .env.test")
    logger.info("Test bootstrap completed. Starting tests...")
    yield
    logger.info("Test Finished!")


# ---------------------------------------------------
# 建立「測試專用 async engine」（共用 dbcon）
# ---------------------------------------------------
@pytest.fixture(scope="session")
async def test_async_engine():
    from app.database import models  # type: ignore

    logger = get_logger(__name__)
    (
        _,
        _,
        _,
        async_engine,
    ) = make_engines(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        db=os.getenv("POSTGRES_DB"),
    )

    # 建schema
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield async_engine

    # tear down
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await async_engine.dispose()
    logger.info("Test DB dropped and engine disposed")


# ---------------------------------------------------
# TestClient + dependency override（關鍵）
# ---------------------------------------------------
@pytest.fixture(scope="function")
def client(test_async_engine: AsyncEngine):
    """
    每個 test function:
    - 使用同一個 async_engine
    - 但 session 是新的
    """

    async def override_get_async_session():
        async for session in get_async_session(test_async_engine)():
            yield session

    # 換插頭: dependency_overrides is a dict where we can define overrides for any dependencies used in our endpoints
    app.dependency_overrides[get_async_session] = override_get_async_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# @pytest.fixture(scope="session", autouse=True)
# async def setup_and_teardown():
#     logger = get_logger(__name__)
#     logger.info("Starting tests...")
#     yield
#     logger.info("Test Finished!")


# @pytest.fixture(scope="module")
# def client():
#     return TestClient(app)
