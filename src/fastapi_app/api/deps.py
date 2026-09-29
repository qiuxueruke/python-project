from typing import Annotated

from fastapi import Depends, HTTPException, status
from jwt import InvalidTokenError
from redis import Redis
from sqlalchemy.orm import Session

from fastapi_app.core.db import get_db
from fastapi_app.core.redis import get_redis
from fastapi_app.core.security import decode_access_token, oauth2_scheme
from fastapi_app.crud import users as user_crud
from fastapi_app.models import User

DbSession = Annotated[Session, Depends(get_db)]
RedisClient = Annotated[Redis, Depends(get_redis)]

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="未登录或登录已过期",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    """从 JWT Token 中解析当前用户（路由里 Depends 注入即受 JWT 保护）。"""
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise _CREDENTIALS_EXCEPTION
        user_id = int(subject)
    except (InvalidTokenError, TypeError, ValueError) as exc:
        raise _CREDENTIALS_EXCEPTION from exc

    user = user_crud.get_by_id(db, user_id)
    if not user:
        raise _CREDENTIALS_EXCEPTION
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
