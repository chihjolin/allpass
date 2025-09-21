import os
import mlflow
from mlflow.pyfunc import PythonModel
from mlflow.tracking import MlflowClient
from dotenv import load_dotenv
from datetime import datetime

import time
import pandas as pd
import shutil

# 建立時間字串 (格式：YYYYMMDD_HHMMSS)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 載入環境變數(開發測試用)
load_dotenv(override=True)

# MLflow Tracking Server
MLFLOW_HOST = os.getenv("MLFLOW_HOST", "localhost")
MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5001")
MLFLOW_URI = f"http://{MLFLOW_HOST}:{MLFLOW_PORT}"
mlflow.set_tracking_uri(MLFLOW_URI)



EXPERIMENT_NAME = f"test_upgrade_new_{timestamp}" 
mlflow.set_experiment(EXPERIMENT_NAME)

# Minio artifact store
MINIO_HOST=os.getenv("MINIO_HOST")
MINIO_PORT=os.getenv("MINIO_PORT")
MINIO_ROOT_USER=os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD=os.getenv("MINIO_ROOT_PASSWORD")
#MINIO_BUCKET_NAME=os.getenv("MINIO_BUCKET_NAME")

AWS_ACCESS_KEY_ID = MINIO_ROOT_USER
AWS_SECRET_ACCESS_KEY = MINIO_ROOT_PASSWORD
MLFLOW_S3_ENDPOINT_URL= f"http://{MINIO_HOST}:{MINIO_PORT}"

#設定環境變數: MLflow 讀 artifact store 設定會讀環境變數
os.environ["AWS_ACCESS_KEY_ID"] = MINIO_ROOT_USER
os.environ["AWS_SECRET_ACCESS_KEY"] = MINIO_ROOT_PASSWORD
os.environ["MLFLOW_S3_ENDPOINT_URL"] = MLFLOW_S3_ENDPOINT_URL
#os.environ["MLFLOW_ARTIFACT_URI"] = f"s3://{MINIO_BUCKET_NAME}"

print("MLflow S3 Endpoint:", os.environ.get("MLFLOW_S3_ENDPOINT_URL"))
print("AWS Access Key:", os.environ.get("AWS_ACCESS_KEY_ID"))
print("AWS Secret Key:", os.environ.get("AWS_SECRET_ACCESS_KEY"))
#print("MLFLOW_ARTIFACT_URI",os.environ.get("MLFLOW_ARTIFACT_URI") )



# --------------------------
# 定義 PythonModel
# --------------------------
class DummyModel(PythonModel):
    def predict(self, context, model_input):
        return model_input


model_name = "upgrade_test_model_new"
client = MlflowClient()



def register_model_with_metric_check(
    model_name: str,
    python_model: PythonModel,
    metric_name: str,
    metric_value: float,
    metric_threshold: float
):
    #client = MlflowClient()
    # --------------------------
    # 開始 MLflow Run
    # --------------------------

    with mlflow.start_run() as run:
        run_id = run.info.run_id
        mlflow.log_param("param1", 123)
        mlflow.log_metric(metric_name, metric_value)

        # 儲存模型
        local_tmppath = "local_model"
        if os.path.exists(local_tmppath):
            shutil.rmtree(local_tmppath)
        mlflow.pyfunc.save_model(path=local_tmppath, python_model=python_model)
        mlflow.log_artifacts(local_tmppath, artifact_path="model")

        # 註冊模型
        model_uri = f"runs:/{run_id}/model"
        result = mlflow.register_model(model_uri=model_uri, name=model_name)
        new_version = result.version

        time.sleep(5)  # 等待模型註冊完成

        # 條件判斷：是否更新 Production
        if metric_value > metric_threshold:
            existing_prod = client.get_latest_versions(name=model_name, stages=["Production"])
            if existing_prod:
                old_version = existing_prod[0].version
                client.transition_model_version_stage(
                    name=model_name,
                    version=old_version,
                    stage="Archived"
                )
                print(f"舊版 {old_version} 已標註為 Archived")

            client.transition_model_version_stage(
                name=model_name,
                version=new_version,
                stage="Production"
            )
            print(f"新版本 {new_version} 已標註為 Production")
        else:
            client.transition_model_version_stage(
                name=model_name,
                version=new_version,
                stage="Staging"
            )
            print(f"新版本 {new_version} 標註為 Staging（未達 Production 標準）")


def load_production_model(model_name:str):    
    """
    從 MLflow Model Registry 載入標註為 Production 的模型，並印出版本號。
    Args:
        model_name (str): 模型註冊名稱  
    Returns:
        model: 可用於預測的 MLflow PyFunc 模型
    """
    try:
        # 查詢 Production 階段的版本
        versions = client.get_latest_versions(name=model_name, stages=["Production"])
        if not versions:
            print(f"模型 '{model_name}' 沒有標註為 Production 的版本")
            return None

        version_info = versions[0]
        version_number = version_info.version
        print(f"模型 '{model_name}' 的 Production 版本為：{version_number}")

        # 載入模型
        model = mlflow.pyfunc.load_model(f"models:/{model_name}/Production")
        print(f"成功載入模型 '{model_name}' 的 Production 版本")
        return model

    
    except Exception as e:
        print(f"載入模型失敗: {e}")
        return None



register_model_with_metric_check(
    model_name="upgrade_test_model_new",
    python_model=DummyModel(),
    metric_name="accuracy",
    metric_value=0.95,
    metric_threshold=0.9
)



# 載入Produciton模型
model = load_production_model(model_name)

if model:
    test_input = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    result = model.predict(test_input)
    print("預測結果:", result)


# # 測試 predict()
# test_input = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
# result = loaded_model.predict(test_input)

# print("✅ Predict 測試結果:")
# print(result)



    # print("Artifact logging 成功")

    # result = mlflow.register_model(
    #     f"runs:/{run_id}/model",
    #     "upgrade_test_model"
    # )

    # print("Model Registry response:", result)


    # --------------------------
    # 直接 log model 到 MinIO 並註冊
    # --------------------------
    # mlflow.pyfunc.log_model(
    #     artifact_path="model",
    #     python_model=DummyModel(),
    #     registered_model_name="upgrade_test_model"
    #     )

    # mlflow.pyfunc.save_model(
    #     path="/tmp/model",   # 先存在容器或本地暫存
    #     python_model=DummyModel()
    # )

    # # 上傳 artifact 到 MinIO
    # mlflow.log_artifacts("/tmp/model", artifact_path="model")


    


# #----Test----
# with mlflow.start_run() as run:
#     print("Run ID:", run.info.run_id)
#     print("Experiment ID:", run.info.experiment_id)

#     # Log 一個參數
#     mlflow.log_param("test_param", 42)

#     # 建立一個測試檔案
#     test_file = "test_artifact.txt"
#     with open(test_file, "w") as f:
#         f.write("hello mlflow artifact test\n")

#     # Log 該檔案為 artifact
#     mlflow.log_artifact(test_file)

#     # 印出 run 的 artifact URI
#     print("Artifact URI:", mlflow.get_artifact_uri())

# print("✅ 測試完成，請到 MinIO bucket & MLflow UI 檢查 run-level artifacts")
# #---Test---