import json
import os
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import r2_score, root_mean_squared_error
from sklearn.model_selection import KFold, RandomizedSearchCV, train_test_split
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import text

from common.utils.dbcon import engine
import mlflow
from dotenv import load_dotenv

# 載入環境變數(開發測試用)
load_dotenv(override=True)

# -----------------------------
# MLflow 設定
# -----------------------------
MLFLOW_HOST = os.getenv("MLFLOW_HOST", "localhost")
MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5001")
MLFLOW_URI = f"http://{MLFLOW_HOST}:{MLFLOW_PORT}"
mlflow.set_tracking_uri(MLFLOW_URI)

EXPERIMENT_NAME = "time_prediction_training"
mlflow.set_experiment(EXPERIMENT_NAME)


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
        pipeline_to_log = {"scaler": scaler, "models": models, "features": X.columns.tolist()}
        # log_model 會自動用 joblib.dump 序列化
        #(1) log 到 run 的 artifacts
        mlflow.pyfunc.log_model(
            artifact_path="model", # 在 MLflow UI 中看到的資料夾名稱
            python_model=TimePredictionModel(pipeline_to_log) # 需要一個包裝類別來符合pyfunc格式
            #registered_model_name="time_prediction_model" # 註冊到 Model Registry
        )
        # #(2) 再用 register_model 註冊
        # mlflow.register_model(
        #     model_uri=f"runs:/{mlflow.active_run().info.run_id}/model",
        #     name="time_prediction_model"
        # )

        #save_pipeline(models, scaler, X.columns.tolist(), metrics)


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
    use_gpu = os.environ.get("USE_XGB_GPU", "1") == "1"
    if use_gpu:
        device_params = {
            "tree_method": "gpu_hist",
            "gpu_id": 0,
            "predictor": "gpu_predictor",
        }
    else:
        device_params = {"tree_method": "hist"}
    base_params.update(device_params)

    # 建立 XGBoost 模型（基底估計器）
    base_xgb = xgb.XGBRegressor(**base_params, n_jobs=max((os.cpu_count() or 2) - 1, 1))

    # 定義超參數搜尋空間
    param_dist = {
        "n_estimators": [100, 200, 300, 400, 500, 800, 1000],
        "max_depth": [3, 4, 5, 6, 7, 8, 10],
        "learning_rate": [0.01, 0.03, 0.05, 0.1, 0.15, 0.2],
        "subsample": [0.8, 0.85, 0.9, 0.95, 1.0],
        "colsample_bytree": [0.8, 0.85, 0.9, 0.95, 1.0],
        "min_child_weight": [1, 3, 5, 7],
        "gamma": [0, 0.1, 0.2, 0.3, 0.4],
        "reg_alpha": [0, 0.1, 0.5, 1.0],
        "reg_lambda": [0, 0.1, 0.5, 1.0, 2.0],
    }

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

    return base_params, random_search.best_params_


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


# def save_pipeline(models, scaler, feature_names, metrics, output_dir="/app/models"):
#     # # 本機測試
#     # output_dir = "./models"
#     os.makedirs(output_dir, exist_ok=True)

#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     model_path = os.path.join(output_dir, f"time_prediction_{timestamp}.pkl")
#     meta_path = os.path.join(output_dir, f"time_prediction_{timestamp}.json")

#     # 保存 pkl (scaler + models + features)
#     joblib.dump(
#         {"scaler": scaler, "models": models, "features": feature_names},
#         model_path,
#     )

#     # 保存 metadata
#     metadata = {"timestamp": timestamp, "metrics": metrics}
#     with open(meta_path, "w") as f:
#         json.dump(metadata, f, indent=2)

#     print(f"模型已保存至 {model_path}")
#     return model_path, meta_path

class TimePredictionModel(mlflow.pyfunc.PythonModel):
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def predict(self, context, model_input):
        # 這裡的 model_input 是 pandas DataFrame
        ordered_df = model_input[self.pipeline['features']]
        scaled_features = self.pipeline['scaler'].transform(ordered_df)
        predictions = [model.predict(scaled_features) for model in self.pipeline['models']]
        return np.mean(predictions, axis=0)


if __name__ == "__main__":
    main()
