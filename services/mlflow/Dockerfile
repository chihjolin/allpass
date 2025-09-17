# services/mlflow/Dockerfile
FROM ghcr.io/mlflow/mlflow:v3.3.2

USER root
# 安裝必要套件（與 ETL 保持一致）
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends curl && \
#     pip install --no-cache-dir psycopg2-binary && \
#     rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    pip install --no-cache-dir psycopg2-binary boto3 "mlflow[s3]" s3fs fsspec && \
    rm -rf /var/lib/apt/lists/*

# 建立 group 和 user，都指定 uid/gid = 1000
RUN groupadd -g 1000 mlflow && \
    useradd -m -u 1000 -g 1000 mlflow

# 切換到 mlflow user
USER 1000:1000
