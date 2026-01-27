import pytest

# from fastapi.testclient import TestClient
from httpx import AsyncClient

from common.utils.logger import get_logger

logger = get_logger(__name__)  # 使用自訂 logger


@pytest.mark.asyncio
async def test_app(async_client: AsyncClient):
    response = await async_client.get("/")
    logger.info("[Response]: %s", response.json())
    assert response.status_code == 200
    assert response.json() == {"detail": "Welcome to Allpass!"}
