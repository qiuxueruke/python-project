from fastapi import APIRouter, HTTPException

from fastapi_app.api.deps import CurrentUser, DbSession
from fastapi_app.models import User
from fastapi_app.schemas import ApiResponse, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["用户信息模块"])


@router.get("/me", response_model=ApiResponse[UserOut])
def get_me(current_user: CurrentUser) -> ApiResponse[UserOut]:
    return ApiResponse.ok(UserOut.model_validate(current_user))


@router.patch("/me", response_model=ApiResponse[UserOut])
def update_me(
    payload: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ApiResponse[UserOut]:
    if payload.nickname is not None:
        current_user.nickname = payload.nickname
    if payload.email is not None:
        current_user.email = payload.email
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return ApiResponse.ok(UserOut.model_validate(current_user))


@router.get("/{user_id}", response_model=ApiResponse[UserOut])
def get_user(user_id: int, db: DbSession) -> ApiResponse[UserOut]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse.ok(UserOut.model_validate(user))
