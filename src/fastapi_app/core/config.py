""" 用 Pydantic Settings 读配置。
字段包括应用名、版本、调试开关、MySQL 连接串、Redis 连接串、token 有效期（默认 24 小时）。
优先读 .env，没有就用代码里的默认值。
get_settings() 用 lru_cache 缓存，整个进程只解析一次。 """
# lru_cache 用来缓存 get_settings() 的结果，避免重复解析配置。
from functools import lru_cache
from pathlib import Path

# BaseSettings 从环境变量和 .env 读取配置；SettingsConfigDict 配置读取行为。
from pydantic_settings import BaseSettings, SettingsConfigDict

# fastapi_app 包根目录（含 static/）。
PACKAGE_DIR = Path(__file__).resolve().parents[1]


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
    # JWT 签名密钥与算法；生产环境必须通过环境变量覆盖密钥。
    jwt_secret_key: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"

    # H5 开发地址，逗号分隔；给 FastAPI CORS 用。
    cors_origins: str = "http://localhost:9000,http://127.0.0.1:9000"

    # 静态资源：磁盘目录与 URL 挂载前缀。
    # static_dir 为空时使用包内 static/；也可写成绝对路径或相对项目启动目录的路径。
    static_dir: str = ""
    static_url: str = "/static"

    # 日志目录；相对路径相对进程启动目录。空字符串表示只打控制台、不写文件。
    log_dir: str = "logs"
    # 单个日志文件上限（字节）与保留份数；超出后滚动改名。
    log_max_bytes: int = 10 * 1024 * 1024
    log_backup_count: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        return origins or ["http://localhost:9000"]

    @property
    def static_path(self) -> Path:
        if self.static_dir.strip():
            path = Path(self.static_dir)
            return path if path.is_absolute() else Path.cwd() / path
        return PACKAGE_DIR / "static"

    # 阿里云 OSS，密钥只放 .env，不要写进代码。
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_endpoint: str = "https://oss-cn-beijing.aliyuncs.com"
    oss_bucket: str = "aliyun-oss-100"
    oss_public_base_url: str = "https://aliyun-oss-100.oss-cn-beijing.aliyuncs.com"


# 整个进程只解析一次配置，后续调用直接返回缓存的 Settings 实例。
@lru_cache
def get_settings() -> Settings:
    return Settings()
