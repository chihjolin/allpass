import logging
import os

# from etl.jobs.join_features import run_join_features_job
from . import join_features, load_geofeatures_to_redis

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

JOB = os.getenv("ETL_JOB", "all")  # 可以透過環境變數指定 job


def main():

    logger.info(f"Runner started, selected job: {JOB}")

    # join_features
    if JOB in ["join_features", "all"]:
        logger.info("Start feature_data job")
        join_features.run_join_features_job()
        logger.info("Finish join_features job")

    # load_geofeatures_to_redis
    if JOB in ["load_geofeatures_to_redis", "all"]:
        logger.info("Start load_geofeatures_to_redis job")
        load_geofeatures_to_redis.run_load_geofeatures_to_redis()
        logger.info("Finish load_geofeatures_to_redis job")


if __name__ == "__main__":
    main()
