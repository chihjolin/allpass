import os
from datetime import datetime

from sqlalchemy import text

from common.utils.dbcon import make_engines
from common.utils.logger import get_logger
from common.utils.redis_client import get_redis_client

# ---------------------------------------------------
# Logging 設定（共用）
# ---------------------------------------------------
logger = get_logger(__name__)  # 使用自訂 logger


def get_env_int(key: str, default: int) -> int:
    value = os.getenv(key)
    return int(value) if value is not None else default


def run_pipeline_test():
    logger.info("=== PIPELINE TEST START ===")

    # =========================
    # Postgres (allpass_db)
    # =========================
    (
        _,
        _,
        engine,
        _,
    ) = make_engines(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        db=os.getenv("POSTGRES_DB"),
    )

    with engine.begin() as conn:
        # 建測試表
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS etl_pipeline_test (
                id SERIAL PRIMARY KEY,
                source VARCHAR(50),
                message TEXT,
                created_at TIMESTAMP
                );
                """
            )
        )

        # insert 一筆
        conn.execute(
            text(
                """
                INSERT INTO etl_pipeline_test (source, message, created_at)
                VALUES (:source, :message, :created_at)
                """
            ),
            {
                "source": "airflow",
                "message": "pipeline ok",
                "created_at": datetime.now(),
            },
        )

    logger.info("Postgres write success")

    # =========================
    # Redis
    # =========================
    redis_client = get_redis_client(
        host=os.getenv("REDIS_HOST", "redis"),
        port=get_env_int("REDIS_PORT", 6379),
        db=get_env_int("REDIS_DB", 1),
    )

    redis_client.set("airflow_pipeline_test", "ok")

    logger.info("Redis write success")
    logger.info("=== PIPELINE TEST END ===")
