"""登录模块：注册、登录、退出。

采用 OAuth2 Password + JWT：
- `/auth/login`、`/auth/register`：`application/x-www-form-urlencoded`（前端）
- `/auth/token`：OAuth2PasswordRequestForm（Swagger Authorize）
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from fastapi_app.api.deps import DbSession
from fastapi_app.core.security import (
    create_access_token,
    hash_password,
    is_legacy_password_hash,
    verify_password,
)
from fastapi_app.crud import users as user_crud
from fastapi_app.models import User
from fastapi_app.schemas.auth import TokenResponse
from fastapi_app.schemas.common import ApiResponse
from fastapi_app.schemas.users import UserOut

router = APIRouter(prefix="/auth", tags=["登录模块"])


def _authenticate_user(db: DbSession, username: str, password: str) -> User | None:
    user = user_crud.get_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    if is_legacy_password_hash(user.password_hash):
        user = user_crud.update_password_hash(db, user, hash_password(password))
    return user


def _issue_token(user: User) -> TokenResponse:
    token, expires_in = create_access_token(
        subject=str(user.id),
        extra_claims={"username": user.username},
    )
    return TokenResponse(token=token, expiresIn=expires_in)


@router.post(
    "/register",
    response_model=ApiResponse[UserOut],
    summary="用户注册",
    description=(
        "表单字段：`username`、`password`（`application/x-www-form-urlencoded`）。"
        "用户名唯一，密码使用 bcrypt 存储。"
    ),
)
def register(
    db: DbSession,
    username: Annotated[str, Form(min_length=1, max_length=64)],
    password: Annotated[str, Form(min_length=1, max_length=128)],
) -> ApiResponse[UserOut]:
    if user_crud.get_by_username(db, username):
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = user_crud.create(
        db,
        username=username,
        password_hash=hash_password(password),
        nickname=username,
    )
    return ApiResponse.ok(UserOut.model_validate(user))


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="用户登录",
    description=(
        "表单字段：`username`、`password`（`application/x-www-form-urlencoded`）。"
        "成功后签发 JWT，返回 `token` / `access_token` 与过期秒数。"
    ),
)
def login(
    db: DbSession,
    username: Annotated[str, Form(min_length=1, max_length=64)],
    password: Annotated[str, Form(min_length=1, max_length=128)],
) -> ApiResponse[TokenResponse]:
    user = _authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ApiResponse.ok(_issue_token(user))


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="用户登录（OAuth2 Password）",
    description=(
        "标准 OAuth2 Password 表单登录，供 Swagger Authorize 使用；"
        "响应直接返回 token 字段（无 ApiResponse 外壳）。"
    ),
)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenResponse:
    user = _authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_token(user)


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    summary="退出登录",
    description="JWT 为无状态令牌，服务端不强制吊销；客户端清除本地 token 即可。",
)
def logout() -> ApiResponse[None]:
    return ApiResponse.ok(message="logged out")
