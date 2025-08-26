import json
import os
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold, RandomizedSearchCV, train_test_split
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import create_engine, text

from common.utils.dbcon import engine

# import warnings


# warnings.filterwarnings("ignore")


def main():
    # 1. 從資料庫撈取資料
    df_features = get_features()
    # 2. 前處理
    X, y, X_train_scaled, X_test_scaled, y_train, y_test, scaler = pre_processing(
        df_features
    )
    # 3. 超參數搜尋
    base_params, best_params = train_model(X_train_scaled, y_train)
    # 4. 訓練集成模型
    models = train_ensemble(X_train_scaled, y_train, base_params, best_params)
    # 5. 評估
    metrics = evaluate(models, X_train_scaled, y_train, X_test_scaled, y_test)
    # 6. 保存模型
    save_pipeline(models, scaler, X.columns.tolist(), metrics)


def get_features():
    """
    載入資料
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
    # # 找出所有 boolean 欄位並轉換成 0/1
    # bool_cols = df.select_dtypes(include=bool).columns
    # df[bool_cols] = df[bool_cols].astype(int)

    return df


def pre_processing(df_features):
    """
    資料正規化
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
    """

    base_params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        # "device": "cuda:0",
        "verbosity": 0,
    }

    use_gpu = os.environ.get("USE_XGB_GPU", "0") == "1"
    if use_gpu:
        device_params = {
            "tree_method": "gpu_hist",
            "gpu_id": 0,
            "predictor": "gpu_predictor",
        }
    else:
        device_params = {"tree_method": "hist"}
    base_params.update(device_params)
    base_xgb = xgb.XGBRegressor(**base_params, n_jobs=os.cpu_count() - 1)

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

    # base_xgb = xgb.XGBRegressor(**base_params)
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    random_search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_dist,
        n_iter=50,
        cv=cv,
        scoring="neg_mean_squared_error",
        n_jobs=1,
        random_state=42,
        verbose=1,
    )

    random_search.fit(X_train_scaled, y_train)

    best_params = random_search.best_params_
    best_score = random_search.best_score_

    print(f"最佳 RMSE: {(-best_score)**0.5:.4f}")

    return base_params, random_search.best_params_


def train_ensemble(X_train_scaled, y_train, base_params, best_params, n_models=5):
    """
    多模型集成 (Ensemble)
    """
    models = []
    for i in range(n_models):
        model = xgb.XGBRegressor(**base_params, **best_params, random_state=42 + i)
        model.fit(X_train_scaled, y_train)
        models.append(model)
    return models


def ensemble_predict(models, X):
    preds = [m.predict(X) for m in models]
    return np.mean(preds, axis=0)


def evaluate(models, X_train, y_train, X_test, y_test):
    """
    評估
    """
    train_pred = ensemble_predict(models, X_train)
    test_pred = ensemble_predict(models, X_test)

    metrics = {
        "train_rmse": mean_squared_error(y_train, train_pred, squared=False),
        "train_r2": r2_score(y_train, train_pred),
        "test_rmse": mean_squared_error(y_test, test_pred, squared=False),
        "test_r2": r2_score(y_test, test_pred),
    }

    print(
        f"訓練 RMSE: {metrics['train_rmse']:.4f}, R²: {metrics['train_r2']:.4f}\n"
        f"測試 RMSE: {metrics['test_rmse']:.4f}, R²: {metrics['test_r2']:.4f}"
    )
    return metrics


def save_pipeline(models, scaler, feature_names, metrics, output_dir="models"):
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = os.path.join(output_dir, f"time_prediction_{timestamp}.pkl")
    meta_path = os.path.join(output_dir, f"time_prediction_{timestamp}.json")

    # 保存 pkl (scaler + models + features)
    joblib.dump(
        {"scaler": scaler, "models": models, "features": feature_names},
        model_path,
    )

    # 保存 metadata
    metadata = {"timestamp": timestamp, "metrics": metrics}
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"模型已保存至 {model_path}")
    return model_path, meta_path


if __name__ == "__main__":
    main()
