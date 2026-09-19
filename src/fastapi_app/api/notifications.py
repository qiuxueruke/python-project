from fastapi import APIRouter, HTTPException

from fastapi_app.api.deps import CurrentUser, DbSession
from fastapi_app.models import Notification
from fastapi_app.schemas import NotificationCreate, NotificationOut

router = APIRouter(prefix="/notifications", tags=["通知模块"])


@router.get("", response_model=list[NotificationOut])
def list_my_notifications(
    current_user: CurrentUser,
    db: DbSession,
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.id.desc())
        .all()
    )


@router.post("", response_model=NotificationOut)
def create_notification(
    payload: NotificationCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Notification:
    # Demo: any logged-in user can create a notification.
    _ = current_user
    item = Notification(
        user_id=payload.user_id,
        title=payload.title,
        content=payload.content,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> Notification:
    item = db.get(Notification, notification_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    item.is_read = 1
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
