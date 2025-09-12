import mlflow
import os
from dotenv import load_dotenv

# 讀取 .env 設定(僅開發測試用)
load_dotenv(override=True)
# dotenv_path = Path(__file__).parent / ".env"
# load_dotenv(dotenv_path=dotenv_path, override=True)

# 組合連線字串
MLFLOW_HOST = os.getenv("MLFLOW_HOST")
MLFLOW_PORT = os.getenv("MLFLOW_PORT")


# MLflow server URI 
MLFLOW_URI = f"http://{MLFLOW_HOST}:{MLFLOW_PORT}"
print(f"mlflow_uri: {MLFLOW_URI}")
mlflow.set_tracking_uri(MLFLOW_URI)

# 指定 experiment
mlflow.set_experiment("time_prediction_import")

# 設定 artifacts 路徑 (後續導入minio)
artifact_dir = os.path.join("..", "services", "mlflow", "mlruns")

# 需要匯入的檔案
artifacts_to_import = [
    "time_prediction_20250828_055526.pkl",
    "time_prediction_20250828_055526.json",
]

with mlflow.start_run(run_name="import_pretrained_model") as run:
    for artifact in artifacts_to_import:
        artifact_path = os.path.join(artifact_dir, artifact)
        if os.path.exists(artifact_path):
            mlflow.log_artifact(artifact_path, artifact_path="artifacts")
            print(f"已匯入 {artifact}")
        else:
            print(f"找不到檔案: {artifact_path}")
    
    print(f"Run ID: {run.info.run_id}")
    print(f"前往 MLflow UI 查看 {MLFLOW_URI}")