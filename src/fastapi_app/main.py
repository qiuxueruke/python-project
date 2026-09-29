"""fastapi_app/main.py"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import fastapi_app.models  # noqa: F401
from fastapi_app.api.router import api_router
from fastapi_app.core.config import get_settings
from fastapi_app.core.db import SessionLocal
from fastapi_app.core.exceptions import register_exception_handlers
# 从 fastapi_app.core.logging 模块中导入 setup_logging 函数 ;用于设置日志配置
from fastapi_app.core.logging import setup_logging
from fastapi_app.core.openapi import APP_DESCRIPTION, OPENAPI_TAGS, setup_openapi
from fastapi_app.core.security import hash_password
from fastapi_app.core.static import register_static_files
from fastapi_app.crud import users as user_crud
from fastapi_app.middleware import RequestLoggingMiddleware
from fastapi_app.schemas.common import ApiResponse


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 表结构由 Alembic 管理：uv run alembic upgrade head
    _ensure_demo_user()
    yield


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
    """
    注册中间件
    :param app: FastAPI 应用
    :return: None
    """
    # 获取设置
    settings = get_settings()
    # 添加 CORS 中间件
    # 后添加的中间件更靠外；日志包住 CORS，便于看到完整请求链路。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|(\d{1,3}\.){3}\d{1,3})(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # 添加请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用
    :return: FastAPI
    """
    # 设置日志配置
    setup_logging()
    # 获取设置
    settings = get_settings()
    # 创建 FastAPI 应用
    app = FastAPI(
        # 应用名称
        title=settings.app_name,
        # 应用版本
        version=settings.app_version,
        # 应用描述
        description=APP_DESCRIPTION,
        # OpenAPI 标签
        openapi_tags=OPENAPI_TAGS,
        # 文档 URL
        docs_url="/docs",
        # 重定向 URL
        redoc_url="/redoc",
        # OpenAPI URL
        openapi_url="/openapi.json",
        # 生命周期
        lifespan=lifespan,
        # Swagger UI 参数
        swagger_ui_parameters={
            # 文档展开方式
            "docExpansion": "list",
            # 默认模型展开深度
            "defaultModelsExpandDepth": 1,
            # 持久化授权
            "persistAuthorization": True,
        },
    )
    # 注册中间件
    register_middlewares(app)
    # 注册异常处理
    register_exception_handlers(app)
    # 包含 API 路由
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
