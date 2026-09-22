"""用户模块 schema。"""
from pydantic import BaseModel, computed_field


class UserOut(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    email: str | None = None
    avatar: str | None = None

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def userId(self) -> int:
        return self.id


class UserUpdate(BaseModel):
    nickname: str | None = None
    email: str | None = None
