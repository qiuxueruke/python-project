""" Pydantic 模型，只描述入参和出参，不写库：

ApiResponse：所有接口共用的外壳，code / message / data
LoginRequest / TokenResponse：注册、登录的用户名密码，以及返回的 token
UserOut / UserUpdate：对外的用户信息（不含密码），以及可改的昵称、邮箱
NotificationOut / NotificationCreate：通知的返回结构和创建入参
UserOut、NotificationOut 开了 from_attributes，可以直接从 SQLAlchemy 对象转出来。 """
# BaseModel 是 Pydantic 的基础模型；Field 用来定义字段约束。
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

# 业务数据的类型参数，由具体接口填成 UserOut、TokenResponse 等。
T = TypeVar("T")


# 统一返回值。成功时 code 为 0；失败时 code 为 HTTP 状态码，data 一般为 null。
class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None

    @classmethod
    def ok(cls, data: T | None = None, message: str = "success") -> "ApiResponse[T]":
        return cls(code=0, message=message, data=data)

    @classmethod
    def fail(
        cls, code: int, message: str, data: object | None = None
    ) -> "ApiResponse[object]":
        return cls(code=code, message=message, data=data)

# 登录、注册入参：用户名和密码。
class LoginRequest(BaseModel):
    # 登录用户名，长度 1 到 64。
    username: str = Field(min_length=1, max_length=64)
    # 登录密码，长度 1 到 128；只出现在入参里，不会出现在返回值中。
    password: str = Field(min_length=1, max_length=128)


# 登录成功后返回的访问令牌。
class TokenResponse(BaseModel):
    # 访问令牌字符串。
    access_token: str
    # 令牌类型，固定为 bearer。
    token_type: str = "bearer"


# 对外返回的用户信息，不含密码。
class UserOut(BaseModel):
    # 用户主键。
    id: int
    # 登录用户名。
    username: str
    # 昵称，可空。
    nickname: str | None = None
    # 邮箱，可空。
    email: str | None = None

    # 允许直接从 SQLAlchemy 的 User 对象转出。
    model_config = {"from_attributes": True}


# 可修改的用户资料：只含昵称和邮箱。
class UserUpdate(BaseModel):
    # 新昵称，可空。
    nickname: str | None = None
    # 新邮箱，可空。
    email: str | None = None


# 通知的返回结构。
class NotificationOut(BaseModel):
    # 通知主键。
    id: int
    # 接收这条通知的用户 id。
    user_id: int
    # 通知标题。
    title: str
    # 通知正文。
    content: str
    # 是否已读：0 未读，1 已读。
    is_read: int
    # 创建时间；用 object 兼容数据库返回的 datetime。
    created_at: object | None = None

    # 允许直接从 SQLAlchemy 的 Notification 对象转出。
    model_config = {"from_attributes": True}


# 创建通知的入参。
class NotificationCreate(BaseModel):
    # 接收这条通知的用户 id。
    user_id: int
    # 通知标题，长度 1 到 128。
    title: str = Field(min_length=1, max_length=128)
    # 通知正文，至少 1 个字符。
    content: str = Field(min_length=1)
