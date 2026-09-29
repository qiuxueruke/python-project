"""Alembic 运行环境：从项目 Settings 读数据库 URL，并挂上全部模型 metadata。"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from fastapi_app.core.config import get_settings
from fastapi_app.core.db import Base

# 导入所有模型，确保 Base.metadata 含有完整表结构。
import fastapi_app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    # 注意：不要用 config.set_main_option 写入含 %40 的 URL，
    # ConfigParser 会把 % 当成插值语法。
    return get_settings().database_url


def run_migrations_offline() -> None:
    """离线模式：只生成 SQL，不连库执行。"""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：连接数据库并执行迁移。"""
    section = config.get_section(config.config_ini_section, {}) or {}
    section["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
