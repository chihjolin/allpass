from typing import Optional

import redis


def get_redis_client(host: str, port: int, password: Optional[str] = None, db: int = 0):
    return redis.Redis(
        host=host,
        port=port,
        password=password,
        db=db,
        decode_responses=True,
    )
