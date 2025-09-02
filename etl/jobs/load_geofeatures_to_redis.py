import os
from decimal import Decimal

from sqlalchemy import text

from common.utils.dbcon import engine
from common.utils.redis_utils import (
    _make_segment_key,
    get_segment_features,
    set_segment_features,
)


def run_load_geofeatures_to_redis():
    """
    1. 從 Postgres 讀取所有 trail_segments
    2. 將 segment features 存入 Redis，key schema:
       trail:{trail_id}:poi:{current_poi_id}:next:{next_poi_id}
    """
    sql_query = """
            SELECT
                trail_id,
                current_poi_id,
                next_poi_id,
                distance,
                elevation_range,
                elevation_change,
                elevation_gain,
                elevation_loss,
                high_elevation,
                max_slope_percent,
                max_slope_degrees,
                slope_std_dev,
                slope_variance,
                max_slope_lat,
                max_slope_lon,
                slope_neg15,
                slope_neg15_neg10,
                slope_neg10_neg5,
                slope_neg5_neg1,
                slope_neg1_1,
                slope_1_5,
                slope_5_10,
                slope_10_15,
                slope_over15,
                accumulated_distance
            FROM ml_features.trail_segments;
    """

    with engine.connect() as conn:
        results = conn.execute(text(sql_query))

    count = 0
    for result in results.mappings():
        # print(result)
        # 1. 拿 key
        trail_id = result["trail_id"]
        current_poi_id = result["current_poi_id"]
        next_poi_id = result["next_poi_id"]
        # 2. 存地理features
        features = {
            k: float(v) if isinstance(v, Decimal) else v
            for k, v in result.items()
            if k not in ("trail_id", "current_poi_id", "next_poi_id")
        }
        key = _make_segment_key(trail_id, current_poi_id, next_poi_id)
        # print("寫入 Redis key:", key, "features:", features)
        # 3. 存進Redis
        set_segment_features(trail_id, current_poi_id, next_poi_id, features)
        count += 1

    print(f"Load complete: {count} segments written to Redis.")


if __name__ == "__main__":
    run_load_geofeatures_to_redis()
