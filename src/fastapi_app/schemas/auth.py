"""登录 / 注册相关 schema。"""
from pydantic import BaseModel, Field, computed_field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """同时兼容前端单 token 字段与 OAuth2 标准字段。"""

    token: str
    expiresIn: int
    token_type: str = "bearer"

    @computed_field
    @property
    def access_token(self) -> str:
        return self.token
