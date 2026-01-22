from fastapi.testclient import TestClient

from common.utils.logger import get_logger

logger = get_logger(__name__)  # 使用自訂 logger


def test_register_success(client: TestClient):
    payload = {
        "email": "user2014@test.com",
        "username": "user2014",
        "password": "my_password14",
    }

    response = client.post("/users/register", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == payload["email"]
    assert "email" in data


def test_register_duplicate_email(client):
    payload = {
        "email": "user2010@test.com",
        "username": "user2010",
        "password": "my_password10",
    }

    response = client.post("/users/register", json=payload)

    assert response.status_code == 400
