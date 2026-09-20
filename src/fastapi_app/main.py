"""fastapi_app/main.py"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi_app.api.router import api_router
from fastapi_app.core.config import get_settings
from fastapi_app.core.db import Base, engine
from fastapi_app.schemas import ApiResponse
import fastapi_app.models  # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 应用生命周期：yield 之前在启动时执行，yield 之后在关闭时执行。
    # Demo only. Prefer Alembic migrations in production.
    try:
        # 按模型元数据创建缺失的数据表，不会修改已存在的表。
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        # 数据库不可用时跳过建表，避免演示环境启动失败。
        print(f"[warn] skip create_all, check MySQL: {exc}")
    # 交还控制权给 FastAPI；此处之后可放置关闭时的清理逻辑。
    yield


def _error_response(code: int, message: str, data: object | None = None) -> JSONResponse:
    body = ApiResponse.fail(code, message, data)
    return JSONResponse(status_code=code, content=jsonable_encoder(body.model_dump()))


def register_exception_handlers(app: FastAPI) -> None:
    # 业务里 raise 的 HTTPException，改成和成功响应一样的外壳。
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request, exc: HTTPException
    ) -> JSONResponse:
        if isinstance(exc.detail, str):
            message, data = exc.detail, None
        else:
            message, data = "请求失败", exc.detail
        response = _error_response(exc.status_code, message, data)
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    # 入参校验失败（缺字段、类型不对）也走同一外壳，明细放在 data 里。
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(422, "请求参数校验失败", exc.errors())


# create_app() 读取配置、创建 FastAPI 实例，挂上 /api 路由，并提供 /health 健康检查。
# 启动时的 lifespan 会调用 Base.metadata.create_all 自动建表（注释写明这只是演示，
# 正式环境应改用 Alembic 迁移）。模块末尾的 app = create_app() 是 uvicorn 加载的对象。
def create_app() -> FastAPI:
    # 读取应用配置（名称、版本等）。
    settings = get_settings()
    # 创建 FastAPI 实例，并绑定启动/关闭生命周期。
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    register_exception_handlers(app)
    # 挂载 /api 路由。
    app.include_router(api_router)

    # 健康检查：用于探活，不依赖数据库。
    @app.get("/health", response_model=ApiResponse[dict[str, str]])
    def health() -> ApiResponse[dict[str, str]]:
        return ApiResponse.ok({"status": "ok"})

    return app


app = create_app()
