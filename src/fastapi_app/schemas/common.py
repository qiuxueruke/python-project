"""通用响应外壳。"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一返回值。成功时 code 为 200；失败时 code 为 HTTP 状态码。"""

    code: int = 200
    message: str = "success"
    data: T | None = None

    # 成功时返回 类方法
    @classmethod
    def ok(cls, data: T | None = None, message: str = "success") -> "ApiResponse[T]":
        """
        :param cls: 类本身
        :param data: 数据
        :param message: 消息
        :return: ApiResponse[T]
        """
        return cls(code=200, message=message, data=data)

    # 失败时返回 类方法
    @classmethod
    def fail(
        cls, code: int, message: str, data: object | None = None
    ) -> "ApiResponse[object]":
        """
        :param cls: 类本身
        :param code: 状态码
        :param message: 消息
        :param data: 数据
        :return: ApiResponse[object]
        """
        return cls(code=code, message=message, data=data)
