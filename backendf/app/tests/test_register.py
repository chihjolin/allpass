from fastapi.testclient import TestClient

from common.utils.logger import get_logger

logger = get_logger(__name__)  # 使用自訂 logger


def test_register_success(client: TestClient, user_payload):
    response = client.post("/users/register", json=user_payload)

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == user_payload["email"]
    assert "username" in data


def test_register_duplicate_email(client, user_payload):

    # 第一次註冊（成功）
    res1 = client.post("/users/register", json=user_payload)
    assert res1.status_code == 201

    # 第二次用「同一個 email」註冊
    res2 = client.post("/users/register", json=user_payload)
    assert res2.status_code == 400
