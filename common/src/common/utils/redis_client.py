import os

import redis


def get_redis_client():
    return redis.Redis(
        # host="localhost",
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", None),
        decode_responses=True,
    )
