"""
ETL Job Template
=================
每個 ETL 任務都可以依照這個模板實作，統一結構：
- main() 為進入點
- 使用 logging 控制輸出
- 加入錯誤處理
"""

import logging
import os
import sys

from utils import dbcon  # 假設你 utils/dbcon.py 有連線函式

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def extract():
    """資料抽取 (Extract)"""
    logger.info("🔹 Extracting data ...")
    # TODO: 加入抽取邏輯，例如從 API / DB 抓資料
    return []


def transform(data):
    """資料轉換 (Transform)"""
    logger.info("🔹 Transforming data ...")
    # TODO: 加入轉換邏輯，例如 pandas 清洗
    return data


def load(data):
    """資料載入 (Load)"""
    logger.info("🔹 Loading data into database ...")
    try:
        engine = dbcon.get_engine()
        # TODO: 例如寫入 PostgreSQL
        # pd.DataFrame(data).to_sql("table_name", con=engine, schema="schema", if_exists="append", index=False)
    except Exception as e:
        logger.error(f"❌ Load failed: {e}")
        raise


def main():
    """ETL Job 主流程"""
    logger.info("🚀 Starting ETL job template")
    try:
        data = extract()
        data = transform(data)
        load(data)
        logger.info("✅ ETL job completed successfully")
    except Exception as e:
        logger.error(f"ETL job failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
