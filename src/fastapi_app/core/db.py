""" SQLAlchemy 的数据库连接。
创建引擎（带连接池探活和 1 小时回收）、会话工厂 SessionLocal、模型基类 Base。
get_db() 是 FastAPI 依赖：每个请求拿一个会话，结束后关闭。 """
# Generator 用来标注 get_db() 是生成器，供 FastAPI 按请求注入并在结束时清理。
from collections.abc import Generator

# create_engine 根据连接串创建带连接池的数据库引擎。
from sqlalchemy import create_engine
# DeclarativeBase 是 ORM 模型基类；Session 表示一次数据库会话；sessionmaker 生产会话。
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# 从配置读取 MySQL 连接串等设置。
from fastapi_app.core.config import get_settings

# 进程内只解析一次配置，后续直接复用缓存结果。
settings = get_settings()

# pool_pre_ping：取出连接前先探活，避免拿到已被服务端断开的连接。
# pool_recycle：连接超过 1 小时就回收重建，防止被数据库空闲超时踢掉。
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 会话工厂：关闭自动提交和自动 flush，由业务代码显式控制事务。
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# 所有 ORM 模型继承此基类，表结构统一登记到 Base.metadata。
class Base(DeclarativeBase):
    pass


# FastAPI 依赖：每个请求单独拿一个会话，结束后无论成败都关闭。
def get_db() -> Generator[Session, None, None]:
    # 为当前请求创建一个数据库会话。
    db = SessionLocal()
    try:
        # 把会话交给路由处理函数使用。
        yield db
    finally:
        # 请求结束时关闭会话，归还连接，避免连接泄漏。
        db.close()
