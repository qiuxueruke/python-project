""" 两张表：

模型	表	作用
User
users
用户：用户名（唯一）、密码哈希、昵称、邮箱、创建时间
Notification
notifications
通知：归属用户、标题、正文、是否已读、创建时间 """

# datetime 用来标注创建时间字段的 Python 类型。
from datetime import datetime

# DateTime、Integer、String、Text 是列类型；func 用来取数据库当前时间。
from sqlalchemy import DateTime, Integer, String, Text, func
# Mapped 标注字段的 Python 类型；mapped_column 把字段映射成表列。
from sqlalchemy.orm import Mapped, mapped_column

# 所有 ORM 模型继承这个基类，表结构统一登记到 Base.metadata。
from fastapi_app.core.db import Base


# 用户表：存账号、密码哈希和可对外展示的资料。
class User(Base):
    __tablename__ = "users"

    # 主键，自增。
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 登录用户名，唯一并建索引，方便按用户名查找。
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # 只存密码哈希，不存明文。
    password_hash: Mapped[str] = mapped_column(String(255))
    # 昵称，可空。
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 邮箱，可空。
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 头像 URL，可空。
    avatar: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # 创建时间，由数据库在插入时填当前时间。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# 通知表：某用户收到的一条消息。
class Notification(Base):
    __tablename__ = "notifications"

    # 主键，自增。
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 接收这条通知的用户 id，建索引方便按用户查询。
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    # 通知标题。
    title: Mapped[str] = mapped_column(String(128))
    # 通知正文，用 Text 以容纳较长内容。
    content: Mapped[str] = mapped_column(Text)
    # 是否已读：0 未读，1 已读，默认未读。
    is_read: Mapped[int] = mapped_column(Integer, default=0)
    # 创建时间，由数据库在插入时填当前时间。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
