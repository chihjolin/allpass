FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir mlflow psycopg2-binary boto3

COPY mlflow_entry.sh /app/mlflow_entry.sh
RUN chmod +x /app/mlflow_entry.sh

EXPOSE 5000

ENTRYPOINT ["/app/mlflow_entry.sh"]
