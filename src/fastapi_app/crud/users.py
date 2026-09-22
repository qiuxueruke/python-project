"""用户表 CRUD。"""
from sqlalchemy.orm import Session

from fastapi_app.models import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create(
    db: Session,
    *,
    username: str,
    password_hash: str,
    nickname: str | None = None,
    email: str | None = None,
) -> User:
    user = User(
        username=username,
        password_hash=password_hash,
        nickname=nickname or username,
        email=email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_profile(
    db: Session,
    user: User,
    *,
    nickname: str | None = None,
    email: str | None = None,
) -> User:
    if nickname is not None:
        user.nickname = nickname
    if email is not None:
        user.email = email
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_avatar(db: Session, user: User, avatar_url: str) -> User:
    user.avatar = avatar_url
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_password_hash(db: Session, user: User, password_hash: str) -> User:
    user.password_hash = password_hash
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
