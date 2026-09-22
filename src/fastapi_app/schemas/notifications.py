"""通知模块 schema。"""
from pydantic import BaseModel, Field


class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    is_read: int
    created_at: object | None = None

    model_config = {"from_attributes": True}


class NotificationCreate(BaseModel):
    user_id: int
    title: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1)
