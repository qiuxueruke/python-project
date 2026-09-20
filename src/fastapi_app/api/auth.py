"""登录模块：注册、登录、退出。

注册把用户名和密码哈希写入 users 表；
登录校验密码后在 Redis 里写入 session token；
退出时按 Authorization 头删除对应的 session。
"""
# hashlib 用来做演示用的密码哈希；生产环境应换成 bcrypt 或 argon2。
import hashlib
# secrets 用来生成不可预测的登录令牌。
import secrets
# Annotated 用来给 Header 参数附加类型和默认值。
from typing import Annotated

# APIRouter 分组路由；Header 读取请求头；HTTPException、status 用来返回错误状态码。
from fastapi import APIRouter, Header, HTTPException, status

# DbSession、RedisClient 是已封装好的数据库会话和 Redis 客户端依赖。
from fastapi_app.api.deps import DbSession, RedisClient
# 读取访问令牌过期时间等配置。
from fastapi_app.core.config import get_settings
# 用户 ORM 模型。
from fastapi_app.models import User
# 登录入参、令牌出参、用户出参。
from fastapi_app.schemas import ApiResponse, LoginRequest, TokenResponse, UserOut

# 登录相关路由，统一挂在 /auth 下。
router = APIRouter(prefix="/auth", tags=["登录模块"])


# 把明文密码变成哈希。这里只用 SHA-256 做演示，生产环境请用 passlib/bcrypt 或 argon2。
def _hash_password(password: str) -> str:
    # 演示用哈希。生产环境请改用 passlib/bcrypt 或 argon2。
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# 注册：用户名已存在则 400，否则写入用户并返回不含密码的资料。
@router.post("/register", response_model=ApiResponse[UserOut])
def register(payload: LoginRequest, db: DbSession) -> ApiResponse[UserOut]:
    # 按用户名查重。
    exists = db.query(User).filter(User.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    # 只存密码哈希，昵称默认用用户名。
    user = User(
        username=payload.username,
        password_hash=_hash_password(payload.password),
        nickname=payload.username,
    )
    db.add(user)
    db.commit()
    # 刷新以拿到数据库生成的 id 和创建时间。
    db.refresh(user)
    return ApiResponse.ok(UserOut.model_validate(user))


# 登录：校验用户名和密码，通过后签发 token 并写入 Redis。
@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(
    payload: LoginRequest, db: DbSession, redis_client: RedisClient
) -> ApiResponse[TokenResponse]:
    # 按用户名取出用户，再比对密码哈希。
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or user.password_hash != _hash_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    settings = get_settings()
    # 生成随机 token，避免可预测。
    token = secrets.token_urlsafe(32)
    # 把 token 映射到用户 id，过期时间按配置的分钟数换算成秒。
    redis_client.setex(
        f"session:{token}",
        settings.access_token_expire_minutes * 60,
        str(user.id),
    )
    return ApiResponse.ok(TokenResponse(access_token=token))


# 退出：从 Authorization 头取出 Bearer token，删除 Redis 里的会话。
@router.post("/logout", response_model=ApiResponse[None])
def logout(
    redis_client: RedisClient,
    authorization: Annotated[str | None, Header()] = None,
) -> ApiResponse[None]:
    # 只处理 Bearer 令牌；没有或格式不对也视为已退出。
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        redis_client.delete(f"session:{token}")
    return ApiResponse.ok(message="logged out")
