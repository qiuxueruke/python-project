"""按模块划分的 Pydantic schema，此处统一再导出便于兼容旧 import。"""
from fastapi_app.schemas.auth import LoginRequest, TokenResponse
from fastapi_app.schemas.common import ApiResponse
from fastapi_app.schemas.notifications import NotificationCreate, NotificationOut
from fastapi_app.schemas.users import UserOut, UserUpdate

__all__ = [
    "ApiResponse",
    "LoginRequest",
    "TokenResponse",
    "UserOut",
    "UserUpdate",
    "NotificationOut",
    "NotificationCreate",
]
