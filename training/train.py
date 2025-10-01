import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
import xgboost as xgb
import yaml
from dotenv import load_dotenv
from mlflow.pyfunc import PythonModel
from mlflow.tracking import MlflowClient
from sklearn.metrics import r2_score, root_mean_squared_error
from sklearn.model_selection import KFold, RandomizedSearchCV, train_test_split
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import text

from common.utils.dbcon import engine

# # 載入環境變數(開發測試用)
# load_dotenv(override=True)


# -----------------------------
# MLflow, MinIO 設定
# -----------------------------
MLFLOW_HOST = os.getenv("MLFLOW_HOST", "mlflow")
MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5000")
MLFLOW_URI = f"http://{MLFLOW_HOST}:{MLFLOW_PORT}"
mlflow.set_tracking_uri(MLFLOW_URI)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# EXPERIMENT_NAME = f"time_prediction_training_{timestamp}"
EXPERIMENT_NAME = f"time_prediction_training_new"
mlflow.set_experiment(EXPERIMENT_NAME)

MINIO_HOST = os.getenv("MINIO_HOST")
MINIO_PORT = os.getenv("MINIO_PORT")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

AWS_ACCESS_KEY_ID = MINIO_ROOT_USER
AWS_SECRET_ACCESS_KEY = MINIO_ROOT_PASSWORD
MLFLOW_S3_ENDPOINT_URL = f"http://{MINIO_HOST}:{MINIO_PORT}"

# 設定環境變數: MLflow 讀 artifact store 設定會讀環境變數
os.environ["AWS_ACCESS_KEY_ID"] = MINIO_ROOT_USER
os.environ["AWS_SECRET_ACCESS_KEY"] = MINIO_ROOT_PASSWORD
os.environ["MLFLOW_S3_ENDPOINT_URL"] = MLFLOW_S3_ENDPOINT_URL

print("MLflow S3 Endpoint:", os.environ.get("MLFLOW_S3_ENDPOINT_URL"))
print("AWS Access Key:", os.environ.get("AWS_ACCESS_KEY_ID"))
print("AWS Secret Key:", os.environ.get("AWS_SECRET_ACCESS_KEY"))

model_name = "time_prediction_model"
base_dir = Path(__file__).parent
hyperparams_path = base_dir / "hyperparams.yaml"

client = MlflowClient()


class TimePredictionModel(mlflow.pyfunc.PythonModel):
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def predict(self, context, model_input):
        # 這裡的 model_input 是 pandas DataFrame
        ordered_df = model_input[self.pipeline["features"]]
        scaled_features = self.pipeline["scaler"].transform(ordered_df)
        predictions = [
            model.predict(scaled_features) for model in self.pipeline["models"]
        ]
        return np.mean(predictions, axis=0)


def main():
    """
    [模型訓練]
    1. 取得特徵資料
    2. 正規化:特徵縮放
    3. 超參數搜尋
    4. 訓練集成模型
    5. 測試集預測
    6. 評估模型表現
    7. 保存模型
    """
    with mlflow.start_run() as run:
        uri = mlflow.get_artifact_uri()
        print("Artifact URI:", uri)
        run_id = run.info.run_id
        print(f"Run ID: {run_id}")

        # 1. 從資料庫撈取資料
        df_features = get_features()
        mlflow.log_param("num_samples", len(df_features))

        # 2. 正規化
        X, y, X_train_scaled, X_test_scaled, y_train, y_test, scaler = pre_processing(
            df_features
        )
        mlflow.log_param("train_data_shape", X_train_scaled.shape)
        mlflow.log_param("test_data_shape", X_test_scaled.shape)

        # 3. 超參數搜尋
        mlflow.log_artifact(hyperparams_path, artifact_path="config")
        base_params, best_params = train_model(X_train_scaled, y_train)
        mlflow.log_params(base_params)
        mlflow.log_params(best_params)

        # 4. 訓練集成模型
        models = train_ensemble(X_train_scaled, y_train, base_params, best_params)

        # 5. 測試集預測
        train_pred = ensemble_predict(models, X_train_scaled)
        test_pred = ensemble_predict(models, X_test_scaled)

        # 6. 評估
        metrics = evaluate(models, y_train, train_pred, y_test, test_pred)
        mlflow.log_metrics(metrics)

        # 7. 保存模型
        pipeline_to_log = {
            "scaler": scaler,
            "models": models,
            "features": X.columns.tolist(),
        }
        register_model_with_metric_check(
            model_name=model_name,
            run_id=run_id,
            python_model=TimePredictionModel(pipeline_to_log),
            metric_name="test_r2",
            metric_value=metrics["test_r2"],
            metric_threshold=0.8,
        )


def get_features():
    """
    取得特徵資料
    """
    with engine.connect() as conn:
        query = """
            SELECT avg_temp, avg_RH, max_precip, distance, elevation_range, 
                elevation_change, elevation_gain, elevation_loss, high_elevation,
                max_slope_percent, max_slope_degrees, slope_std_dev, slope_variance,
                max_slope_lat, max_slope_lon, slope_neg15, slope_neg15_neg10, 
                slope_neg10_neg5, slope_neg5_neg1, slope_neg1_1, slope_1_5, 
                slope_5_10, slope_10_15, slope_over15, accumulated_time_seconds, 
                accumulated_distance, spend_time_seconds from ml_features.time_prediction;
        """
        result = conn.execute(text(query)).mappings().all()

    df = pd.DataFrame(result)
    return df


def pre_processing(df_features):
    """
    正規化
    """
    X = df_features.drop(columns="spend_time_seconds")
    y = df_features["spend_time_seconds"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X, y, X_train_scaled, X_test_scaled, y_train, y_test, scaler


def train_model(X_train_scaled, y_train):
    """
    模型訓練 (含超參數搜尋)
    1. 建立基礎參數決定GPU / CPU 訓練策略
    2. 建立 XGBoost 模型（基底估計器）
    3. 定義超參數搜尋空間
    4. 建立 KFold 交叉驗證器
    5. 用 RandomizedSearchCV 做隨機搜尋 + 交叉驗證
    6. 以訓練資料 .fit() 執行搜尋
    7. 取出最佳參數與分數，並把分數轉為 RMSE 印出
    8. 回傳「基礎參數」與「最佳參數」
    """

    base_params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        # "device": "cuda:0",
        "verbosity": 0,
    }

    # 依環境決定 GPU / CPU 訓練策略: 本機跑訓練用GPU, 容器跑先用CPU
    use_gpu = os.environ.get("USE_XGB_GPU", "0") == "1"
    if use_gpu:
        device_params = {
            "tree_method": "gpu_hist",
            "gpu_id": 0,
            "predictor": "cpu_predictor",
        }
    else:
        device_params = {"tree_method": "hist"}
    base_params.update(device_params)

    # 建立 XGBoost 模型（基底估計器）
    base_xgb = xgb.XGBRegressor(**base_params, n_jobs=max((os.cpu_count() or 2) - 1, 1))

    # 定義超參數搜尋空間
    with open(hyperparams_path) as f:
        param_dist = yaml.safe_load(f)
    print(param_dist)

    # 建立 KFold 交叉驗證器
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    # 用 RandomizedSearchCV 做隨機搜尋 + 交叉驗證
    random_search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_dist,
        n_iter=50,
        cv=cv,
        scoring="neg_mean_squared_error",
        # n_jobs=1,
        random_state=42,
        verbose=1,
    )

    # 以訓練資料 .fit() 執行搜尋
    random_search.fit(X_train_scaled, y_train)

    # 取出最佳參數與分數，並把分數轉為 RMSE 印出
    best_params = random_search.best_params_
    best_score = random_search.best_score_

    print(f"最佳 RMSE: {(-best_score)**0.5:.4f}")

    return base_params, best_params


def train_ensemble(X_train_scaled, y_train, base_params, best_params, n_models=5):
    """
    多模型集成 (Ensemble)
    「利用同樣的最佳參數，改變隨機種子，訓練多個略有差異的 XGBoost 模型」，最後透過集成降低預測方差、提升泛化表現
    1.接收最佳參數
    2.建立多個 XGBoost 模型，隨機種子不同
    3.各模型分別在同一訓練集上擬合
    4.收集模型，回傳成一個 ensemble 模型清單
    5.後續推理時，可以取多模型預測的平均值，降低單一模型的方差，增強穩定性。
    """
    models = []
    for i in range(n_models):
        model = xgb.XGBRegressor(**base_params, **best_params, random_state=42 + i)
        model.fit(X_train_scaled, y_train)
        models.append(model)
    return models


def ensemble_predict(models, X):
    """
    把多個子模型的預測合併成單一預測值的函式-回傳各子模型的預測平均(也可考慮:根據每個模型在驗證集上的表現給權重計算加權平均）
    """
    preds = [m.predict(X) for m in models]
    return np.mean(preds, axis=0)


def evaluate(models, y_train, train_pred, y_test, test_pred):
    """
    計算常見的迴歸評估指標（RMSE 與 R²）
    """
    metrics = {
        "train_rmse": root_mean_squared_error(y_train, train_pred),
        "train_r2": r2_score(y_train, train_pred),
        "test_rmse": root_mean_squared_error(y_test, test_pred),
        "test_r2": r2_score(y_test, test_pred),
    }

    print(
        f"訓練 RMSE: {metrics['train_rmse']:.4f}, R²: {metrics['train_r2']:.4f}\n"
        f"測試 RMSE: {metrics['test_rmse']:.4f}, R²: {metrics['test_r2']:.4f}"
    )
    # 後續: metrics 寫到 log 或監控系統（MLflow / prometheus / DB），並保留 best_params、model_hash 以利追溯
    return metrics


def register_model_with_metric_check(
    model_name: str,
    run_id: str,
    python_model: PythonModel,
    metric_name: str,
    metric_value: float,
    metric_threshold: float,
):
    """
    註冊模型並根據指定 metric 是否超過門檻來決定是否標註為 Production。
    """
    try:
        client = MlflowClient()
        # 儲存模型
        local_tmppath = "local_model"
        if os.path.exists(local_tmppath):
            shutil.rmtree(local_tmppath)
        mlflow.pyfunc.save_model(path=local_tmppath, python_model=python_model)
        mlflow.log_artifacts(local_tmppath, artifact_path="model")
        model_uri = mlflow.get_artifact_uri("model")
        print("模型儲存位置:", model_uri)

        # 註冊模型
        model_uri = f"runs:/{run_id}/model"
        result = mlflow.register_model(model_uri=model_uri, name=model_name)
        new_version = result.version

        time.sleep(5)  # 等待模型註冊完成

        # 條件判斷：是否更新 Production
        if metric_value > metric_threshold:
            existing_prod = client.get_latest_versions(
                name=model_name, stages=["Production"]
            )
            if existing_prod:
                old_version = existing_prod[0].version
                client.transition_model_version_stage(
                    name=model_name, version=old_version, stage="Archived"
                )
                print(f"舊版 {old_version} 已標註為 Archived")

            client.transition_model_version_stage(
                name=model_name, version=new_version, stage="Production"
            )
            print(f"新版本 {new_version} 已標註為 Production")
        else:
            client.transition_model_version_stage(
                name=model_name, version=new_version, stage="Staging"
            )
            print(f"新版本 {new_version} 標註為 Staging（未達 Production 標準）")
    except Exception as e:
        print(f"模型註冊失敗: {e}")


if __name__ == "__main__":
    main()
