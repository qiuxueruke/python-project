import hashlib
import secrets
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from fastapi_app.api.deps import DbSession, RedisClient
from fastapi_app.core.config import get_settings
from fastapi_app.models import User
from fastapi_app.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["登录模块"])


def _hash_password(password: str) -> str:
    # Demo hash only. Use passlib/bcrypt (or argon2) in production.
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@router.post("/register", response_model=UserOut)
def register(payload: LoginRequest, db: DbSession) -> User:
    exists = db.query(User).filter(User.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=payload.username,
        password_hash=_hash_password(payload.password),
        nickname=payload.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest, db: DbSession, redis_client: RedisClient
) -> TokenResponse:
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or user.password_hash != _hash_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    settings = get_settings()
    token = secrets.token_urlsafe(32)
    redis_client.setex(
        f"session:{token}",
        settings.access_token_expire_minutes * 60,
        str(user.id),
    )
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(
    redis_client: RedisClient,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        redis_client.delete(f"session:{token}")
    return {"message": "logged out"}
