from fastapi import APIRouter

from fastapi_app.api import auth, notifications, users
from fastapi_app.schemas.common import ApiResponse

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(notifications.router)


@api_router.get(
    "/health",
    tags=["健康检查"],
    summary="API 健康检查",
    description="检查 `/api` 路由是否可用，不依赖数据库与 Redis。",
)
def health() -> ApiResponse[dict[str, str]]:
    return ApiResponse.ok({"status": "ok"})
