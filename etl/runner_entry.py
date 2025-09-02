# etl/runner_entry.py
import logging
import os
import time

from etl.init import init_postgres
from etl.jobs.runner import main as run_jobs

# 本機測試用
# from init import init_postgres
# from jobs.runner import main as run_jobs


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

INIT_FLAG = "/app/etl/init/init_done.flag"


def main():

    # 1. 初始化資料庫
    logger.info("Starting DB initialization...")
    success = init_postgres.main()  # 執行 init/init_postgres.py
    if success:
        with open(INIT_FLAG, "w") as f:
            f.write("done")
        logger.info("DB initialization complete.")
    else:
        logger.error("DB initialization failed, flag not written.")

    # # 2. 等待 init 完成 (若未來要支援多個 container 搶同一個 init，就需要保留 loop)
    # while not os.path.exists(INIT_FLAG):
    #     time.sleep(1)

    # 3. 執行指定 job
    ETL_JOB = os.getenv("ETL_JOB", "all")  # 可透過環境變數指定, 預設為所有jobs
    os.environ["ETL_JOB"] = ETL_JOB
    logger.info(f"Triggering job: {ETL_JOB}")
    run_jobs()
    logger.info(f"{ETL_JOB} done.")

    # 4. 讓 container 不退出（持續 idle）
    # while True:
    #     time.sleep(3600)  # 每小時睡一次


if __name__ == "__main__":
    main()
