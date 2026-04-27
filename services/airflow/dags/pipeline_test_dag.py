from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime

default_args ={
    "retries": 1,
}

with DAG(
    dag_id="pipeline_test",
    start_date=datetime(2026, 4, 26),
    # schedule="0 22 * * *",
    schedule=None,
    catchup=False,
)as dag:
    
    run_pipeline_test = DockerOperator(
        task_id="run_pipeline_test",
        docker_url="unix://var/run/docker.sock",
        image="your-etl-image:latest",  # ⚠️ 你自己的 ETL image (要自建)
        command="python -m jobs.runner",
        environment={
            "JOB": "pipeline_test",

            # DB
            "POSTGRES_HOST": "postgis",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "allpass_db",
            "POSTGRES_USER": "allpass_user",
            "POSTGRES_PASSWORD": "allpass",

            # Redis
            "REDIS_HOST": "redis",
            "REDIS_DB": "1",
        },
        network_mode="allpass-network",  # ⚠️ 很重要
        auto_remove="success",
    )