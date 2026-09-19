from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "fastapi-app"
    app_version: str = "0.1.0"
    debug: bool = True

    # @ in the password must be URL-encoded as %40
    database_url: str = (
        "mysql+pymysql://root:MyStrongP%40ss123@47.100.188.66:3306/fastapi_app"
    )

    redis_url: str = "redis://:MyRedisP%40ss123@47.100.188.66:6379/0"

    access_token_expire_minutes: int = 60 * 24


@lru_cache
def get_settings() -> Settings:
    return Settings()
