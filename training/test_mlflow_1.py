import os
import mlflow
from mlflow.pyfunc import PythonModel
from dotenv import load_dotenv

# 載入環境變數(開發測試用)
load_dotenv(override=True)

# MLflow Tracking Server
MLFLOW_HOST = os.getenv("MLFLOW_HOST", "localhost")
MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5001")
MLFLOW_URI = f"http://{MLFLOW_HOST}:{MLFLOW_PORT}"
mlflow.set_tracking_uri(MLFLOW_URI)


EXPERIMENT_NAME = "test_upgrade_new"
mlflow.set_experiment(EXPERIMENT_NAME)

# Minio artifact store
MINIO_HOST=os.getenv("MINIO_HOST")
MINIO_PORT=os.getenv("MINIO_PORT")
MINIO_ROOT_USER=os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD=os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET_NAME=os.getenv("MINIO_BUCKET_NAME")

AWS_ACCESS_KEY_ID = MINIO_ROOT_USER
AWS_SECRET_ACCESS_KEY = MINIO_ROOT_PASSWORD
MLFLOW_S3_ENDPOINT_URL= f"http://{MINIO_HOST}:{MINIO_PORT}"

#設定環境變數: MLflow 讀 artifact store 設定會讀環境變數
os.environ["AWS_ACCESS_KEY_ID"] = MINIO_ROOT_USER
os.environ["AWS_SECRET_ACCESS_KEY"] = MINIO_ROOT_PASSWORD
os.environ["MLFLOW_S3_ENDPOINT_URL"] = MLFLOW_S3_ENDPOINT_URL
os.environ["MLFLOW_ARTIFACT_URI"] = f"s3://{MINIO_BUCKET_NAME}"

print("MLflow S3 Endpoint:", os.environ.get("MLFLOW_S3_ENDPOINT_URL"))
print("AWS Access Key:", os.environ.get("AWS_ACCESS_KEY_ID"))
print("AWS Secret Key:", os.environ.get("AWS_SECRET_ACCESS_KEY"))
print("MLFLOW_ARTIFACT_URI",os.environ.get("MLFLOW_ARTIFACT_URI") )

with mlflow.start_run() as run:
    uri = mlflow.get_artifact_uri()
    print("Artifact URI:", uri)

# --------------------------
# 定義 PythonModel
# --------------------------
class DummyModel(PythonModel):
    def predict(self, context, model_input):
        return model_input

# --------------------------
# 開始 MLflow Run
# --------------------------

with mlflow.start_run() as run:
    print(f"Run ID: {run.info.run_id}")
    # Log params / metrics
    mlflow.log_param("param1", 123)
    mlflow.log_metric("metric1", 0.99)

    # --------------------------
    # 直接 log model 到 MinIO 並註冊
    # --------------------------
    mlflow.pyfunc.log_model(
        artifact_path="model",
        python_model=DummyModel(),
        registered_model_name="upgrade_test_model"
        )

    # mlflow.pyfunc.save_model(
    #     path="/tmp/model",   # 先存在容器或本地暫存
    #     python_model=DummyModel()
    # )

    # # 上傳 artifact 到 MinIO
    # mlflow.log_artifacts("/tmp/model", artifact_path="model")


    


