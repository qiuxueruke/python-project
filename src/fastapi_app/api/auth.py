"""登录模块：注册、登录、退出。

采用 OAuth2 Password + JWT：
- `/auth/login`：JSON 登录，给前端用
- `/auth/token`：表单登录，给 Swagger OAuth2 Password 用
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
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
from fastapi_app.schemas.auth import LoginRequest, TokenResponse
from fastapi_app.schemas.common import ApiResponse
from fastapi_app.schemas.users import UserOut

router = APIRouter(prefix="/auth", tags=["登录模块"])


def _authenticate_user(db: DbSession, username: str, password: str) -> User | None:
    user = user_crud.get_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    # 旧 SHA-256 哈希在登录成功后升级为 bcrypt。
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
    description="用户名唯一。密码使用 bcrypt 存储，成功后返回用户资料（不含密码）。",
)
def register(payload: LoginRequest, db: DbSession) -> ApiResponse[UserOut]:
    if user_crud.get_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = user_crud.create(
        db,
        username=payload.username,
        password_hash=hash_password(payload.password),
        nickname=payload.username,
    )
    return ApiResponse.ok(UserOut.model_validate(user))


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="用户登录（JSON）",
    description="校验用户名与密码后签发 JWT。返回 `token` / `access_token` 与过期秒数。",
)
def login(payload: LoginRequest, db: DbSession) -> ApiResponse[TokenResponse]:
    user = _authenticate_user(db, payload.username, payload.password)
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
        "标准 OAuth2 Password 表单登录（`application/x-www-form-urlencoded`）。"
        "供 Swagger Authorize 使用；响应同时含 `access_token` 与 `token`。"
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
