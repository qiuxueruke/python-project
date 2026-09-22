"""fastapi_app/main.py"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

import fastapi_app.models  # noqa: F401
from fastapi_app.api.router import api_router
from fastapi_app.core.config import get_settings
from fastapi_app.core.db import Base, SessionLocal, engine
from fastapi_app.core.exceptions import register_exception_handlers
from fastapi_app.core.logging import setup_logging
from fastapi_app.core.openapi import APP_DESCRIPTION, OPENAPI_TAGS, setup_openapi
from fastapi_app.core.security import hash_password
from fastapi_app.core.static import register_static_files
from fastapi_app.crud import users as user_crud
from fastapi_app.middleware import RequestLoggingMiddleware
from fastapi_app.schemas.common import ApiResponse


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Demo only. Prefer Alembic migrations in production.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] skip create_all, check MySQL: {exc}")
    _ensure_user_avatar_column()
    _ensure_demo_user()
    yield


def _ensure_user_avatar_column() -> None:
    try:
        inspector = inspect(engine)
        if "users" not in inspector.get_table_names():
            return
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "avatar" in columns:
            return
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar VARCHAR(512) NULL"))
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] skip add avatar column: {exc}")


def _ensure_demo_user() -> None:
    db = SessionLocal()
    try:
        if user_crud.get_by_username(db, "demo"):
            return
        user_crud.create(
            db,
            username="demo",
            password_hash=hash_password("123456"),
            nickname="演示用户",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] skip demo user: {exc}")
    finally:
        db.close()


def register_middlewares(app: FastAPI) -> None:
    settings = get_settings()
    # 后添加的中间件更靠外；日志包住 CORS，便于看到完整请求链路。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|(\d{1,3}\.){3}\d{1,3})(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=APP_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        swagger_ui_parameters={
            "docExpansion": "list",
            "defaultModelsExpandDepth": 1,
            "persistAuthorization": True,
        },
    )
    register_middlewares(app)
    register_exception_handlers(app)
    app.include_router(api_router)
    setup_openapi(app)
    # 静态目录挂载放在路由之后；注意 mount 是兜底匹配，勿盖住 /api。
    register_static_files(app)

    @app.get(
        "/health",
        tags=["健康检查"],
        summary="根路径健康检查",
        description="用于容器 / 负载均衡探活，不访问数据库。",
        response_model=ApiResponse[dict[str, str]],
    )
    def health() -> ApiResponse[dict[str, str]]:
        return ApiResponse.ok({"status": "ok"})

    return app


app = create_app()
