from fastapi import APIRouter, HTTPException

from fastapi_app.api.deps import CurrentUser, DbSession
from fastapi_app.crud import notifications as notification_crud
from fastapi_app.schemas.common import ApiResponse
from fastapi_app.schemas.notifications import NotificationCreate, NotificationOut

router = APIRouter(prefix="/notifications", tags=["通知模块"])


@router.get(
    "",
    response_model=ApiResponse[list[NotificationOut]],
    summary="我的通知列表",
    description="返回当前登录用户的通知，按 id 倒序。",
)
def list_my_notifications(
    current_user: CurrentUser,
    db: DbSession,
) -> ApiResponse[list[NotificationOut]]:
    items = notification_crud.list_by_user_id(db, current_user.id)
    return ApiResponse.ok([NotificationOut.model_validate(item) for item in items])


@router.post(
    "",
    response_model=ApiResponse[NotificationOut],
    summary="创建通知",
    description="登录用户可创建通知；演示环境暂不做权限细分。",
)
def create_notification(
    payload: NotificationCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[NotificationOut]:
    _ = current_user
    item = notification_crud.create(
        db,
        user_id=payload.user_id,
        title=payload.title,
        content=payload.content,
    )
    return ApiResponse.ok(NotificationOut.model_validate(item))


@router.post(
    "/{notification_id}/read",
    response_model=ApiResponse[NotificationOut],
    summary="标记通知已读",
    description="仅能标记属于当前用户的通知；不存在或不属于自己时返回 404。",
)
def mark_read(
    notification_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> ApiResponse[NotificationOut]:
    item = notification_crud.get_by_id(db, notification_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="通知不存在")
    item = notification_crud.mark_read(db, item)
    return ApiResponse.ok(NotificationOut.model_validate(item))
