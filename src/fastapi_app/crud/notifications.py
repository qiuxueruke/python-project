"""通知表 CRUD。"""
from sqlalchemy.orm import Session

from fastapi_app.models import Notification


def get_by_id(db: Session, notification_id: int) -> Notification | None:
    return db.get(Notification, notification_id)


def list_by_user_id(db: Session, user_id: int) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.id.desc())
        .all()
    )


def create(
    db: Session,
    *,
    user_id: int,
    title: str,
    content: str,
) -> Notification:
    item = Notification(
        user_id=user_id,
        title=title,
        content=content,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def mark_read(db: Session, item: Notification) -> Notification:
    item.is_read = 1
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
