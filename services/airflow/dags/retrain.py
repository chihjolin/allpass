from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

default_args = {"retries": 1, "retry_delay": timedelta(minutes=5)}
with DAG(
    dag_id="time_pred_retrain",
    default_args=default_args,
    start_date=datetime(2025, 8, 29),  # 直接指定日期
    schedule=None,  # Airflow 3.x 正確參數名稱
    catchup=False,
) as dag:

    etl_join = DockerOperator(
        task_id="etl_join_features",
        image="ghcr.io/you/etl:latest",
        command="python -m jobs.runner",
        environment={"JOB": "join_features", "ENV": "prod"},
        network_mode="your_net",
        auto_remove="success",
    )

    load_geo = DockerOperator(
        task_id="etl_load_geofeatures",
        image="ghcr.io/you/etl:latest",
        command="python -m jobs.runner",
        environment={"JOB": "load_geofeatures_to_redis", "ENV": "prod"},
        network_mode="your_net",
        auto_remove="success",
    )

    # train = DockerOperator(
    #     task_id="train_model",
    #     image="ghcr.io/you/train:latest",  # 你的訓練鏡像
    #     command="python train.py",
    #     environment={
    #         "MLFLOW_TRACKING_URI": "http://mlflow:5000",
    #         # 其他資料庫/MinIO/參數
    #     },
    #     network_mode="your_net",
    #     auto_remove=True,
    # )

    # evaluate_and_register = DockerOperator(
    #     task_id="evaluate_and_register",
    #     image="ghcr.io/you/train:latest",
    #     command="python promote_if_better.py",  # 內含比較 → transition_to(Production)
    #     environment={"MLFLOW_TRACKING_URI": "http://mlflow:5000"},
    #     network_mode="your_net",
    #     auto_remove=True,
    # )

    # notify_reload = DockerOperator(
    #     task_id="notify_predict_reload",
    #     image="curlimages/curl:8.9.0",
    #     command="-X POST http://time-predict:8000/reload",
    #     network_mode="your_net",
    #     auto_remove=True,
    # )

    # [etl_join, load_geo] >> train >> evaluate_and_register >> notify_reload
    [etl_join, load_geo]
