"""通用响应外壳。"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一返回值。成功时 code 为 0；失败时 code 为 HTTP 状态码。"""

    code: int = 0
    message: str = "success"
    data: T | None = None

    @classmethod
    def ok(cls, data: T | None = None, message: str = "success") -> "ApiResponse[T]":
        return cls(code=0, message=message, data=data)

    @classmethod
    def fail(
        cls, code: int, message: str, data: object | None = None
    ) -> "ApiResponse[object]":
        return cls(code=code, message=message, data=data)
