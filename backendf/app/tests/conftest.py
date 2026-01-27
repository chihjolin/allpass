import asyncio
import os
import uuid
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from app.main import app  # type: ignore
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlmodel import SQLModel

from common.utils.dbcon import get_async_session as async_session_factory
from common.utils.dbcon import make_engines
from common.utils.logger import get_logger
from common.utils.logger_config import setup_logging

# ---------------------------------------------------
# 整體測試流程
# pytest 啟動 → 載入 .env.test → 建立測試用 async_engine → 建 schema →
# 每個 test function 用 override 把 app 原本的 DB session 換成測試 DB →
# test 結束後 drop schema
# ---------------------------------------------------


# ---------------------------------------------------
# pytest 啟動時載入logging, .env.test設定
# ---------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def test_bootstrap():
    setup_logging()
    logger = get_logger(__name__)
    env_path = Path(__file__).parent / ".env.test"
    load_dotenv(dotenv_path=env_path, override=True)
    logger.info("Loaded .env.test")
    logger.info("Test bootstrap completed. Starting tests...")
    yield
    logger.info("Test Finished!")


# ---------------------------------------------------
# 建立「測試專用 async engine」（共用 dbcon）
# ---------------------------------------------------
# @pytest_asyncio.fixture(scope="session")
# @pytest_asyncio.fixture(scope="function")
@pytest.fixture(scope="session")
async def test_async_engine():
    """
    建立全域測試用的 AsyncEngine，並負責 Schema 的建立與拆除
    """
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

    # ---------- setup ----------
    # 建 schema + tables
    async with async_engine.begin() as conn:
        # 建立 schema（若不存在）
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS user_gpx"))
        # 建立table
        await conn.run_sync(SQLModel.metadata.create_all)

    yield async_engine

    # ---------- teardown ----------
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        # await conn.execute(text("DROP SCHEMA IF EXISTS user_gpx CASCADE"))

    await async_engine.dispose()
    logger.info("Test DB dropped and engine disposed")


# ---------------------------------------------------
# AsyncClient + dependency override（關鍵）
# ---------------------------------------------------
@pytest.fixture
# @pytest_asyncio.fixture(scope="function")
async def async_client(
    test_async_engine: AsyncEngine,
) -> AsyncGenerator[AsyncClient, None]:
    from app.api.dependencies import get_async_session  # type: ignore

    # 1. 準備 Override 函式
    # async_session_factory 回傳的是一個 dependency function (closure)
    override_get_async_session = async_session_factory(test_async_engine)

    # # 未來引入 transaction / rollback 使用以下版本
    # async def override_get_async_session():
    #     # async for ... yield session: 轉接 AsyncGenerator(_get_async_session) 給 FastAPI
    #     async for session in async_session_factory(test_async_engine)():
    #         yield session

    # 2. 換插頭: dependency_overrides is a dict where we can define overrides for any dependencies used in our endpoints
    # Override production DB dependency with test DB session
    app.dependency_overrides[get_async_session] = override_get_async_session

    # 3. 啟動 AsyncClient
    # ASGITransport 讓請求直接在記憶體中傳遞給 FastAPI app，不走網路
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client
    finally:
        # 4. 清理, 避免測試失敗時 overrides 沒清乾淨
        app.dependency_overrides.clear()


@pytest.fixture
def user_payload():
    uid = uuid.uuid4().hex[:8]
    return {
        "email": f"user_{uid}@test.com",
        "username": f"user_{uid}",
        "password": "my_password",
    }
