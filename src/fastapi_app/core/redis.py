from collections.abc import Generator

import redis

from fastapi_app.core.config import get_settings

settings = get_settings()

redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def get_redis() -> Generator[redis.Redis, None, None]:
    yield redis_client
