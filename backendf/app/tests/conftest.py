# import logging

import pytest
from app.main import app  # type: ignore
from fastapi.testclient import TestClient

from common.utils.logger import get_logger
from common.utils.logger_config import setup_logging


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    setup_logging()


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown():
    logger = get_logger(__name__)
    logger.info("Starting tests...")
    yield
    logger.info("Test Finished!")


@pytest.fixture(scope="module")
def client():
    return TestClient(app)
