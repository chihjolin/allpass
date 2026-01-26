# import pytest_asyncio
import asyncio
import os
import uuid
from pathlib import Path

import pytest
from app.main import app  # type: ignore
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio.engine import AsyncEngine

# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from common.utils.dbcon import get_async_session as async_session_factory
from common.utils.dbcon import make_engines
from common.utils.logger import get_logger
from common.utils.logger_config import setup_logging

# from httpx import ASGITransport, AsyncClient

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
    # load_dotenv(".env.test", override=True)
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
    from app.api.dependencies import get_async_session  # type: ignore

    override_get_async_session = async_session_factory(test_async_engine)

    # 未來引入 transaction / rollback 使用以下版本
    # async def override_get_async_session():
    #     # async for ... yield session: 轉接 AsyncGenerator(_get_async_session) 給 FastAPI
    #     async for session in async_session_factory(test_async_engine)():
    #         yield session

    # 換插頭: dependency_overrides is a dict where we can define overrides for any dependencies used in our endpoints
    # Override production DB dependency with test DB session
    app.dependency_overrides[get_async_session] = override_get_async_session

    try:
        with TestClient(app) as client:
            yield client
    finally:
        # 避免測試失敗時 overrides 沒清乾淨
        app.dependency_overrides.clear()


@pytest.fixture
def user_payload():
    uid = uuid.uuid4().hex[:8]
    return {
        "email": f"user_{uid}@test.com",
        "username": f"user_{uid}",
        "password": "my_password",
    }
