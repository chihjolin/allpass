import pandas as pd
from sqlalchemy import text

from common.utils.dbcon import engine

# 特徵工程程式

# === 1. 讀取 CSV ===
df = pd.read_csv(f"./feature_data_new.csv")

# === ETL 清洗 ===
df.columns = [c.lower() for c in df.columns]  # 欄位名稱轉小寫

df.to_sql(
    name="time_prediction",  # 表格名稱
    schema="ml_features",  # Schema
    con=engine,
    if_exists="append",  # append / replace / fail
    index=False,
    method="multi",  # 批次 INSERT 提速
    chunksize=1000,  # 一批 1000 筆
)

print("CSV 批次匯入完成！")
