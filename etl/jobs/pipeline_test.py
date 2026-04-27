import os
import psycopg2
import redis
from datetime import datetime
import logging


def run_pipeline_test():
    print("=== PIPELINE TEST START ===")

    # -------- Postgres --------
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgis"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "allpass_db"),
        user=os.getenv("POSTGRES_USER", "allpass_user"),
        password=os.getenv("POSTGRES_PASSWORD", "allpass"),
    )

    cur = conn.cursor()

    # 建測試表
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS etl_pipeline_test (
        id SERIAL PRIMARY KEY,
        source VARCHAR(50),
        message TEXT,
        created_at TIMESTAMP
        );
        """
    )

    # insert 一筆
    cur.execute(
    """
        INSERT INTO etl_pipeline_test (source, message, created_at)
        VALUES (%s, %s, %s)
        """,
    ("airflow", "pipeline ok", datetime.now()),
    )

    conn.commit()
    cur.close()
    conn.close()

    print("Postgres write success")

    # -------- Redis --------
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=6379,
        db=int(os.getenv("REDIS_DB", 1)),
    )

    r.set("airflow_pipeline_test", "ok")

    print("Redis write success")
    print("=== PIPELINE TEST END ===")