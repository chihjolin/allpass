import mlflow
import os
from dotenv import load_dotenv
from pathlib import Path

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

# host 上 artifact 原始目錄
host_artifact_dir = Path(__file__).parent / ".." / "mlruns"
print(host_artifact_dir)

# 需要匯入的檔案
artifacts_to_import = [
    "time_prediction_20250828_055526.pkl",
    "time_prediction_20250828_055526.json",
]

with mlflow.start_run(run_name="import_pretrained_model") as run:
    for filename in artifacts_to_import:
        artifact_path = host_artifact_dir / filename
        if artifact_path.exists():
            # 直接將 host 上 artifact 上傳，artifact_path="artifacts" 會放在 MLflow artifact root 下
            mlflow.log_artifact(str(artifact_path), artifact_path="artifacts")
            print(f"已匯入 {artifact_path.name}")
        else:
            print(f"找不到檔案: {artifact_path}")

    print(f"Run ID: {run.info.run_id}")
    print(f"前往 MLflow UI 查看 {MLFLOW_URI}")



# with mlflow.start_run(run_name="import_pretrained_model") as run:
#     for artifact_filename in artifacts_to_import:
#         # 構造本地檔案的完整路徑
#         local_file_path = host_artifact_dir / artifact_filename
        
#         if local_file_path.exists():
#             #print(f"local_path: {local_file_path}")
#             # 第一個參數是您要上傳的本地檔案路徑
#             # 第二個參數 (artifact_path) 是希望在 MLflow UI 的 artifacts 中顯示的路徑結構
#             # 如果設為 "artifacts"，所有檔案都會被放到一個名為 artifacts 的子目錄下
#             mlflow.log_artifact(local_file_path, artifact_path="imported_models")
#             print(f"已匯入 {artifact_filename}")
#         else:
#             print(f"找不到檔案: {local_file_path}")

#     run_id = run.info.run_id
#     print(f"Run ID: {run_id}")
#     print(f"Artifacts logged to run with ID: {run_id}")
#     print(f"前往 MLflow UI 查看 {MLFLOW_URI}/#/experiments/{mlflow.get_experiment_by_name('time_prediction_import').experiment_id}/runs/{run_id}")

# # # 為了 HTTP server，先 copy 到臨時目錄，container 可讀
# # tmp_dir = Path("/tmp/mlflow_artifacts")
# # tmp_dir.mkdir(parents=True, exist_ok=True)

# # for filename in artifacts_to_import:
# #     src = host_artifact_dir / filename
# #     dst = tmp_dir / filename
# #     if src.exists():
# #         shutil.copy(src, dst)
# #         print(f"已複製到臨時目錄: {dst}")
# #     else:
# #         raise FileNotFoundError(f"找不到檔案: {src}")
    

# # # -----------------------------
# # # 4️⃣ 上傳 artifact 到 MLflow server
# # # -----------------------------
# # with mlflow.start_run(run_name="import_pretrained_model") as run:
# #     for filename in artifacts_to_import:
# #         artifact_path = tmp_dir / filename
# #         # artifact_path="artifacts" 會放在 MLflow server artifact root 下的 artifacts 資料夾
# #         mlflow.log_artifact(str(artifact_path), artifact_path="artifacts")
# #         print(f"已匯入 {artifact_path.name}")

# #     print(f"Run ID: {run.info.run_id}")
# #     print(f"前往 MLflow UI 查看 {MLFLOW_URI}")


# # with mlflow.start_run(run_name="import_pretrained_model") as run:
# #     for artifact in artifacts_to_import:
# #         artifact_path = os.path.join(artifact_dir, artifact)
# #         if os.path.exists(artifact_path):
# #             mlflow.log_artifact(artifact_path, artifact_path="artifacts")
# #             print(f"已匯入 {artifact}")
# #         else:
# #             print(f"找不到檔案: {artifact_path}")
    
# #     print(f"Run ID: {run.info.run_id}")
# #     print(f"前往 MLflow UI 查看 {MLFLOW_URI}")