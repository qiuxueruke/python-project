""" 用 Pydantic Settings 读配置。
字段包括应用名、版本、调试开关、MySQL 连接串、Redis 连接串、token 有效期（默认 24 小时）。
优先读 .env，没有就用代码里的默认值。
get_settings() 用 lru_cache 缓存，整个进程只解析一次。 """
# lru_cache 用来缓存 get_settings() 的结果，避免重复解析配置。
from functools import lru_cache

# BaseSettings 从环境变量和 .env 读取配置；SettingsConfigDict 配置读取行为。
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 优先读取项目根目录的 .env；忽略未声明的额外字段，避免多余环境变量报错。
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用名称与版本，用于 FastAPI 文档标题等展示。
    app_name: str = "fastapi-app"
    app_version: str = "0.1.0"
    # 调试开关；生产环境应在 .env 中设为 false。
    debug: bool = True

    # 密码中的 @ 必须 URL 编码为 %40，否则会被当成用户名与主机的分隔符。
    # MySQL 连接串，供 SQLAlchemy 创建引擎使用。
    database_url: str = (
        "mysql+pymysql://root:MyStrongP%40ss123@47.100.188.66:3306/fastapi_app"
    )

    # Redis 连接串；密码同样需要把 @ 编码为 %40。
    redis_url: str = "redis://:MyRedisP%40ss123@47.100.188.66:6379/0"

    # 访问令牌有效期，默认 24 小时（60 * 24 分钟）。
    access_token_expire_minutes: int = 60 * 24


# 整个进程只解析一次配置，后续调用直接返回缓存的 Settings 实例。
@lru_cache
def get_settings() -> Settings:
    return Settings()
