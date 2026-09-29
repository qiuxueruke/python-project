"""密码哈希与 JWT / OAuth2 工具。"""
# 导入 UTC、datetime、timedelta 模块
from datetime import UTC, datetime, timedelta
from typing import Any

# 导入 bcrypt 模块
import bcrypt
# 导入 jwt 模块
import jwt
from fastapi.security import OAuth2PasswordBearer

# 导入 get_settings 配置
from fastapi_app.core.config import get_settings

# Swagger「Authorize」走 OAuth2 Password；受保护路由 Depends(oauth2_scheme) 强制带 Bearer。
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def hash_password(password: str) -> str:
    """
    哈希密码
    :param password: 密码
    :return: 哈希密码
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验密码；兼容旧版 SHA-256 哈希，登录成功后由调用方升级为 bcrypt。"""
    if not hashed_password:
        return False
    if hashed_password.startswith("$2"):
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except ValueError:
            return False
    # 旧演示哈希：sha256 hex
    import hashlib

    digest = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return digest == hashed_password


def is_legacy_password_hash(hashed_password: str) -> bool:
    """
    检查密码是否为旧版哈希
    :param hashed_password: 哈希密码
    :return: 是否为旧版哈希
    """
    return bool(hashed_password) and not hashed_password.startswith("$2")


def create_access_token(
    subject: str,
    *,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> tuple[str, int]:
    """签发 JWT，返回 (token, expires_in_seconds)。"""
    settings = get_settings()
    expires_minutes = settings.access_token_expire_minutes
    expire_delta = expires_delta or timedelta(minutes=expires_minutes)
    expires_in = int(expire_delta.total_seconds())
    expire_at = datetime.now(UTC) + expire_delta
    payload: dict[str, Any] = {"sub": subject, "exp": expire_at}
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """
    解码 JWT
    :param token: JWT
    :return: 解码后的 JWT
    """
    settings = get_settings()
    # 解码 JWT，使用设置的密钥和算法
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
