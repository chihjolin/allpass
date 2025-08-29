import json
import os

import redis

from common.utils.redis_client import get_redis_client

# ===== Redis 初始化 =====
redis_client = get_redis_client()
print(redis_client.ping())


# ===== Key schema helper =====
def _make_segment_key(trail_id: int, current_poi_id: int, next_poi_id: int) -> str:
    return f"trail:{trail_id}:poi:{current_poi_id}:next:{next_poi_id}"


# ===== 存資料 =====
def set_segment_features(
    trail_id: int, current_poi_id: int, next_poi_id: int, features: dict
):
    key = _make_segment_key(trail_id, current_poi_id, next_poi_id)
    redis_client.hset(
        key, mapping={k: str(v) for k, v in features.items() if v is not None}
    )
    if redis_client.exists(key):
        print(f"Saved in Redis: {key}")
    else:
        print(f"Failed to save: {key}")


# ===== 取資料 =====
def get_segment_features(
    trail_id: int, current_poi_id: int, next_poi_id: int
) -> dict | None:
    key = _make_segment_key(trail_id, current_poi_id, next_poi_id)
    if redis_client.exists(key):
        return redis_client.hgetall(key)  # dict
    return None


# ===== Key schema helper: session_uuid =====
def _make_session_uuid_key(trail_id: int, user_id: int, date: str) -> str:
    return f"trail:{trail_id}:user:{user_id}:date:{date}"


# === 存本次爬山session_uuid ==
def set_session_uuid(trail_id: int, user_id: int, date: str, session_uuid: str):
    key = _make_session_uuid_key(trail_id, user_id, date)
    redis_client.set(key, session_uuid, ex=86400)  # 設1天TTL
    if redis_client.exists(key):
        print(f"Saved session_uuid in Redis: {key}")
    else:
        print(f"Failed to save session_uuid: {key}")


# === 取本次爬山session_uuid ==
def get_session_uuid(trail_id: int, user_id: int, date: str) -> str | None:
    key = _make_session_uuid_key(trail_id, user_id, date)
    if redis_client.exists(key):
        return redis_client.get(key)
    else:
        return None


# ===== 測試用 =====
if __name__ == "__main__":
    # 存一筆
    sample_features = {"distance": 1.2, "elevation_gain": 150, "max_slope_percent": 25}
    set_segment_features(101, 10, 11, sample_features)

    # 取一筆
    features = get_segment_features(101, 10, 11)
    print("Redis 取出:", features)

    # 第一次經過通訊點，產生新 session_uuid
    session_uuid = "4f6466d4-d5a7-4fe9-869e-a4b8d5779455"
    set_session_uuid(
        trail_id=101, user_id=999, date="20250829", session_uuid=session_uuid
    )

    # 後續經過通訊點，就從 Redis 查
    existing = get_session_uuid(trail_id=101, user_id=999, date="20250829")
    print("查到的 session:", existing)
