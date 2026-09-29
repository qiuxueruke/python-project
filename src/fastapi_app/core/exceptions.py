"""全局异常处理：统一成 ApiResponse 外壳。"""
import logging

# 导入 FastAPI 和 Request
from fastapi import FastAPI, HTTPException, Request
# 导入 jsonable_encoder 可以将 Pydantic 模型转换为 JSON 格式
from fastapi.encoders import jsonable_encoder
# 导入 RequestValidationError 请求参数验证错误
from fastapi.exceptions import RequestValidationError
# 导入 JSONResponse 响应 JSON 数据
from fastapi.responses import JSONResponse
# 导入 StarletteHTTPException 星际网异常
from starlette.exceptions import HTTPException as StarletteHTTPException
# 导入 ApiResponse 响应外壳
from fastapi_app.schemas.common import ApiResponse

# 使用 logging.getLogger 获取名为 "fastapi_app.exception" 的日志记录器
logger = logging.getLogger("fastapi_app.exception")


def _error_response(
    code: int, message: str, data: object | None = None
) -> JSONResponse:
    """
    错误响应
    :param code: 状态码
    :param message: 消息
    :param data: 数据
    :return: JSONResponse
    """
    body = ApiResponse.fail(code, message, data)
    return JSONResponse(status_code=code, content=jsonable_encoder(body.model_dump()))


def register_exception_handlers(app: FastAPI) -> None:
    """
    注册异常处理
    :param app: FastAPI 应用
    :return: None
    """
    # 注册 HTTP 异常处理
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """
        HTTP 异常处理
        :param request: 请求
        :param exc: 异常
        :return: JSONResponse
        """
        if isinstance(exc.detail, str):
            message, data = exc.detail, None
        else:
            message, data = "请求失败", exc.detail
        # *后面的参数只能通过关键字传参，不能通过位置传参
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
        """
        StarletteHTTPException 异常处理
        :param request: 请求
        :param exc: 异常
        :return: JSONResponse
        """
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
        """
        请求参数校验失败异常处理
        :param request: 请求
        :param exc: 异常
        :return: JSONResponse
        """
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
        """
        未处理异常处理
        :param request: 请求
        :param exc: 异常
        :return: JSONResponse
        """
        logger.exception(
            "unhandled_exception request_id=%s path=%s",
            getattr(request.state, "request_id", "-"),
            request.url.path,
        )
        return _error_response(500, "服务器内部错误")
