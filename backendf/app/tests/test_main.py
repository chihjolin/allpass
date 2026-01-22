# import logging

from fastapi.testclient import TestClient

from common.utils.logger import get_logger

logger = get_logger(__name__)  # 使用自訂 logger


def test_app(client: TestClient):
    response = client.get("/")
    logger.info("[Response]: %s", response.json())
    # print("[Response]:", response.json())
    assert response.status_code == 200
    assert response.json() == {"detail": "Welcome to Allpass!"}
