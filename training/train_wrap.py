# train.py (修正版)
import json
import os
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, RandomizedSearchCV, train_test_split
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import text

from common.utils.dbcon import engine

# 假設 engine 已在別處定義並可 import，或在此建立
# from common.db import engine


# --------------- helper wrapper ---------------
class TimePredictionModel:
    """
    包裝 scaler + ensemble models + feature list，
    在部署時只要 joblib.load 並呼叫 .predict(df_or_array)
    """

    def __init__(self, scaler, models, feature_names, model_version=None):
        self.scaler = scaler
        self.models = models
        self.feature_names = feature_names
        self.model_version = model_version

    def predict_from_dataframe(self, df):
        # df: pandas DataFrame with columns containing feature_names
        X = df[self.feature_names].values
        X_scaled = self.scaler.transform(X)
        preds = np.mean([m.predict(X_scaled) for m in self.models], axis=0)
        return preds

    def predict_from_array(self, X_array):
        X_scaled = self.scaler.transform(X_array)
        preds = np.mean([m.predict(X_scaled) for m in self.models], axis=0)
        return preds


# --------------- 1) data load ---------------
def get_features(source="db", sql_path=None):
    """
    讀取特徵。預設從 DB 讀取(使用 engine)，或給 csv 路徑讀取。
    """
    if source == "csv":
        assert sql_path is not None
        df = pd.read_csv(sql_path)
    else:
        query = """
            SELECT avg_temp, avg_RH, max_precip, distance, elevation_range, 
                elevation_change, elevation_gain, elevation_loss, high_elevation,
                max_slope_percent, max_slope_degrees, slope_std_dev, slope_variance,
                max_slope_lat, max_slope_lon, slope_neg15, slope_neg15_neg10, 
                slope_neg10_neg5, slope_neg5_neg1, slope_neg1_1, slope_1_5, 
                slope_5_10, slope_10_15, slope_over15, accumulated_time_seconds, 
                accumulated_distance, spend_time_seconds 
            FROM ml_features.time_prediction;
        """
        with engine.connect() as conn:
            result = conn.execute(text(query)).mappings().all()
        df = pd.DataFrame(result)

    # convert boolean-like columns to int (robust version)
    for col in df.columns:
        if df[col].dropna().isin([0, 1, True, False]).all():
            df[col] = df[col].astype(int)

    # check NaNs
    nan_summary = df.isna().sum()
    if nan_summary.any():
        print(
            "Warning: columns with NaN found:", nan_summary[nan_summary > 0].to_dict()
        )
        # 這裡簡單處理：填中位數（視情況改用更合理的策略）
        for c in df.columns:
            if df[c].isna().sum() > 0:
                df[c].fillna(df[c].median(), inplace=True)

    return df


# --------------- 2) preprocessing ---------------
def pre_processing(df_features, test_size=0.2, random_state=42):
    """
    回傳 X (DataFrame), y (Series), scaler, X_train_scaled, X_test_scaled, y_train, y_test
    """
    if "spend_time_seconds" not in df_features.columns:
        raise ValueError("Missing target column 'spend_time_seconds'")

    X = df_features.drop(columns="spend_time_seconds")
    y = df_features["spend_time_seconds"]

    # Optional: 如果 target 非常偏態，可以 log1p 轉換
    # from scipy import stats
    # if y.skew() > 1.0:
    #     y = np.log1p(y)
    #     note in metadata

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return {
        "X": X,
        "y": y,
        "scaler": scaler,
        "X_train_scaled": X_train_scaled,
        "X_test_scaled": X_test_scaled,
        "y_train": y_train,
        "y_test": y_test,
        "feature_names": X.columns.tolist(),
    }


# --------------- 3) hyperparam search ---------------
def train_model(X_train_scaled, y_train, use_gpu=False, n_iter=50, n_jobs=None):
    """
    回傳 base_params 與 best_params；並印出 CV 統計
    """
    base_params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "verbosity": 0,
    }

    if use_gpu:
        # GPU config for xgboost sklearn wrapper
        base_params.update(
            {"tree_method": "gpu_hist", "gpu_id": 0, "predictor": "gpu_predictor"}
        )
    else:
        base_params.update({"tree_method": "hist"})

    # n_jobs for XGBoost itself (parallel threads)
    base_params["n_jobs"] = max(1, (os.cpu_count() or 1) - 1)

    param_dist = {
        "n_estimators": [100, 200, 300, 400, 500, 800],
        "max_depth": [3, 4, 5, 6, 7, 8],
        "learning_rate": [0.01, 0.03, 0.05, 0.1, 0.2],
        "subsample": [0.8, 0.9, 1.0],
        "colsample_bytree": [0.8, 0.9, 1.0],
        "min_child_weight": [1, 3, 5],
        "gamma": [0, 0.1, 0.2],
        "reg_alpha": [0, 0.1, 0.5],
        "reg_lambda": [0, 0.1, 1.0],
    }

    base_xgb = xgb.XGBRegressor(**base_params)
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    # 如果沒有特別限制，可以把 n_jobs 設為 -1（但在 container 要注意）
    if n_jobs is None:
        n_jobs = 1  # 或 os.cpu_count()-1 或 -1 依容器資源

    random_search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_dist,
        n_iter=n_iter,
        cv=cv,
        scoring="neg_mean_squared_error",
        n_jobs=n_jobs,
        random_state=42,
        verbose=1,
    )

    random_search.fit(X_train_scaled, y_train)

    best_params = random_search.best_params_
    best_score = random_search.best_score_
    print(f"RandomizedSearchCV best RMSE (cv): {(-best_score)**0.5:.4f}")

    # optional: show top 3 param sets
    results = random_search.cv_results_
    ranked_idx = np.argsort(results["mean_test_score"])[::-1][:3]
    print("Top 3 CV candidates (mean_test_score):")
    for i in ranked_idx:
        print(i, results["params"][i], "mean_score:", results["mean_test_score"][i])

    return base_params, best_params, random_search


# --------------- 4) ensemble training ---------------
def train_ensemble(X_train_scaled, y_train, base_params, best_params, n_models=5):
    models = []
    for i in range(n_models):
        # use different random seeds to create variation
        params = dict(best_params)
        params["random_state"] = 42 + i
        # merge base_params except tree_method/n_jobs handled in best_params possibly
        model = xgb.XGBRegressor(**base_params, **params)
        model.fit(X_train_scaled, y_train)
        models.append(model)
    return models


# --------------- evaluate ---------------
def evaluate(models, X_train_scaled, y_train, X_test_scaled, y_test):
    train_pred = np.mean([m.predict(X_train_scaled) for m in models], axis=0)
    test_pred = np.mean([m.predict(X_test_scaled) for m in models], axis=0)

    metrics = {
        "train_rmse": mean_squared_error(y_train, train_pred, squared=False),
        "train_r2": r2_score(y_train, train_pred),
        "train_mae": mean_absolute_error(y_train, train_pred),
        "test_rmse": mean_squared_error(y_test, test_pred, squared=False),
        "test_r2": r2_score(y_test, test_pred),
        "test_mae": mean_absolute_error(y_test, test_pred),
    }

    print(
        f"訓練 RMSE: {metrics['train_rmse']:.4f}, R²: {metrics['train_r2']:.4f}, MAE: {metrics['train_mae']:.4f}\n"
        f"測試  RMSE: {metrics['test_rmse']:.4f}, R²: {metrics['test_r2']:.4f}, MAE: {metrics['test_mae']:.4f}"
    )
    return metrics


# --------------- save pipeline ---------------
def save_pipeline(
    models,
    scaler,
    feature_names,
    metrics,
    best_params,
    search_obj=None,
    output_dir="models",
):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_version = f"v{timestamp}"
    model_filename = os.path.join(output_dir, f"time_prediction_{model_version}.pkl")
    meta_filename = os.path.join(output_dir, f"time_prediction_{model_version}.json")

    # 包成 wrapper 物件
    wrapper = TimePredictionModel(
        scaler=scaler,
        models=models,
        feature_names=feature_names,
        model_version=model_version,
    )

    joblib.dump(wrapper, model_filename)

    # metadata
    metadata = {
        "timestamp": timestamp,
        "model_version": model_version,
        "metrics": metrics,
        "best_params": best_params,
        "package_versions": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "xgboost": xgb.__version__,
        },
    }

    if search_obj is not None:
        # 儲存 top cv info
        metadata["cv_mean_test_score"] = float(search_obj.best_score_)

    with open(meta_filename, "w") as f:
        json.dump(metadata, f, indent=2)

    print("Saved model:", model_filename)
    print("Saved metadata:", meta_filename)
    return model_filename, meta_filename


# --------------- main ---------------
def main():
    # reproducibility
    SEED = 42
    np.random.seed(SEED)
    # sklearn random states passed in constructors above

    # 1) load features (db or csv)
    df = get_features(source="db")

    # 2) preprocess
    prep = pre_processing(df, test_size=0.2, random_state=SEED)
    X = prep["X"]
    feature_names = prep["feature_names"]
    scaler = prep["scaler"]
    X_train_scaled = prep["X_train_scaled"]
    X_test_scaled = prep["X_test_scaled"]
    y_train = prep["y_train"]
    y_test = prep["y_test"]

    # 3) hyperparam search (detect GPU via env)
    use_gpu = os.environ.get("USE_XGB_GPU", "0") == "1"
    base_params, best_params, search_obj = train_model(
        X_train_scaled, y_train, use_gpu=use_gpu, n_iter=30, n_jobs=1
    )

    # 4) train ensemble
    models = train_ensemble(
        X_train_scaled, y_train, base_params, best_params, n_models=5
    )

    # 5) evaluate
    metrics = evaluate(models, X_train_scaled, y_train, X_test_scaled, y_test)

    # 6) save
    save_pipeline(
        models,
        scaler,
        feature_names,
        metrics,
        best_params,
        search_obj=search_obj,
        output_dir="models",
    )


if __name__ == "__main__":
    main()
