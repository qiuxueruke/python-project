from fastapi import APIRouter

from fastapi_app.api import auth, notifications, users

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(notifications.router)
