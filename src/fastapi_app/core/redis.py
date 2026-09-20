""" 全局 Redis 客户端，decode_responses=True 让取出的值是字符串。get_redis() 把这个客户端注入到请求里，登录态就存在这里。 """
# Generator 用来标注 get_redis() 是生成器，供 FastAPI 按请求注入。
from collections.abc import Generator

# redis 客户端库，用来连接 Redis。
import redis

# 从配置读取 Redis 连接串。
from fastapi_app.core.config import get_settings

# 进程内只解析一次配置，后续直接复用缓存结果。
settings = get_settings()

# 全局 Redis 客户端；decode_responses=True 让取出的值直接是字符串，而不是字节。
redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


# FastAPI 依赖：把全局客户端注入到请求里，登录态存在 Redis 中。
def get_redis() -> Generator[redis.Redis, None, None]:
    # 交出同一个客户端；连接池由 redis-py 自己管理，这里不关闭。
    yield redis_client
