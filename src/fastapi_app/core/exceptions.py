"""全局异常处理：统一成 ApiResponse 外壳。"""
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi_app.schemas.common import ApiResponse

logger = logging.getLogger("fastapi_app.exception")


def _error_response(
    code: int, message: str, data: object | None = None
) -> JSONResponse:
    body = ApiResponse.fail(code, message, data)
    return JSONResponse(status_code=code, content=jsonable_encoder(body.model_dump()))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        if isinstance(exc.detail, str):
            message, data = exc.detail, None
        else:
            message, data = "请求失败", exc.detail
        logger.warning(
            "http_exception request_id=%s status=%s detail=%s path=%s",
            getattr(request.state, "request_id", "-"),
            exc.status_code,
            exc.detail,
            request.url.path,
        )
        response = _error_response(exc.status_code, message, data)
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "请求失败"
        logger.warning(
            "starlette_http_exception request_id=%s status=%s detail=%s path=%s",
            getattr(request.state, "request_id", "-"),
            exc.status_code,
            exc.detail,
            request.url.path,
        )
        return _error_response(exc.status_code, message)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            "validation_error request_id=%s path=%s errors=%s",
            getattr(request.state, "request_id", "-"),
            request.url.path,
            exc.errors(),
        )
        return _error_response(422, "请求参数校验失败", exc.errors())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "unhandled_exception request_id=%s path=%s",
            getattr(request.state, "request_id", "-"),
            request.url.path,
        )
        return _error_response(500, "服务器内部错误")
