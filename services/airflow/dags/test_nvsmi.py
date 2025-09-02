from datetime import datetime

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import DeviceRequest, Mount  # 需要 docker-py >= 5.x

with DAG(
    dag_id="test_env_new",
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    gpu_test = DockerOperator(
        task_id="print_nvidia_smi",
        docker_url="unix://var/run/docker.sock",
        image="nvidia/cuda:12.4.1-runtime-ubuntu22.04",
        command="nvidia-smi",
        auto_remove="force",
        mount_tmp_dir=False,
        device_requests=[DeviceRequest(count=-1, capabilities=[["gpu"]])],
    )

    print_ls_info = DockerOperator(
        task_id="print_ls_info",
        docker_url="unix://var/run/docker.sock",
        image="nvidia/cuda:12.4.1-runtime-ubuntu22.04",
        command="ls /home/zoe",
        mounts=[
            Mount(target="/home/zoe", source="/home/zoe", type="bind", read_only=False)
        ],
        auto_remove="force",
        mount_tmp_dir=False,
        device_requests=[DeviceRequest(count=-1, capabilities=[["gpu"]])],
    )

    print_hello = DockerOperator(
        task_id="print_hello",
        docker_url="unix://var/run/docker.sock",
        image="nvidia/cuda:12.4.1-runtime-ubuntu22.04",
        command="echo hello",
        auto_remove="force",
        mount_tmp_dir=False,
        device_requests=[DeviceRequest(count=-1, capabilities=[["gpu"]])],
    )

    [gpu_test, print_hello] >> print_ls_info
