"""按模块划分的数据库操作函数。"""
from fastapi_app.crud import notifications, users

__all__ = ["users", "notifications"]
