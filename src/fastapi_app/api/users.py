from fastapi import APIRouter, File, HTTPException, UploadFile

from fastapi_app.api.deps import CurrentUser, DbSession
from fastapi_app.core.oss import MAX_AVATAR_BYTES, delete_by_public_url, upload_avatar
from fastapi_app.crud import users as user_crud
from fastapi_app.schemas.common import ApiResponse
from fastapi_app.schemas.users import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["用户信息模块"])


@router.get(
    "/me",
    response_model=ApiResponse[UserOut],
    summary="获取当前用户",
    description="根据 Bearer token 返回当前登录用户资料。",
)
def get_me(current_user: CurrentUser) -> ApiResponse[UserOut]:
    return ApiResponse.ok(UserOut.model_validate(current_user))


@router.patch(
    "/me",
    response_model=ApiResponse[UserOut],
    summary="更新当前用户资料",
    description="可修改昵称、邮箱；未传的字段保持不变。",
)
def update_me(
    payload: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ApiResponse[UserOut]:
    user = user_crud.update_profile(
        db,
        current_user,
        nickname=payload.nickname,
        email=payload.email,
    )
    return ApiResponse.ok(UserOut.model_validate(user))


@router.post(
    "/me/avatar",
    response_model=ApiResponse[UserOut],
    summary="上传头像",
    description="上传图片到 OSS，更新当前用户头像 URL；单文件不超过 5MB。",
)
def upload_my_avatar(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> ApiResponse[UserOut]:
    content = file.file.read(MAX_AVATAR_BYTES + 1)
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=400, detail="头像不能超过 5MB")

    old_avatar = current_user.avatar
    avatar_url = upload_avatar(content, current_user.id)
    user = user_crud.update_avatar(db, current_user, avatar_url)
    delete_by_public_url(old_avatar)
    return ApiResponse.ok(UserOut.model_validate(user))


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserOut],
    summary="按 ID 获取用户",
    description="返回指定用户的公开资料；用户不存在时返回 404。",
)
def get_user(user_id: int, db: DbSession) -> ApiResponse[UserOut]:
    user = user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ApiResponse.ok(UserOut.model_validate(user))
