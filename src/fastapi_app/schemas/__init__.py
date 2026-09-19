from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    email: str | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    nickname: str | None = None
    email: str | None = None


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
