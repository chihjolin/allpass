# from fastapi.testclient import TestClient
import pytest
from httpx import AsyncClient

from common.utils.logger import get_logger

logger = get_logger(__name__)  # 使用自訂 logger


# @pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient, user_payload):
    response = await async_client.post("/users/register", json=user_payload)

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == user_payload["email"]
    assert "username" in data


# @pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient, user_payload):

    # 第一次註冊（成功）
    res1 = await async_client.post("/users/register", json=user_payload)
    assert res1.status_code == 201

    # 第二次用「同一個 email」註冊（預期失敗）
    res2 = await async_client.post("/users/register", json=user_payload)
    assert res2.status_code == 400
