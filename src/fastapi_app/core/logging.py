"""应用日志配置。"""
# logging 模块是 Python 标准库中的一个模块，用于记录日志。
# 它提供了一个灵活的日志系统，可以记录不同级别（DEBUG、INFO、WARNING、ERROR、CRITICAL）的日志信息。
# 日志可以记录到文件、控制台、网络等不同的输出目标。
# 日志级别从低到高依次为 DEBUG、INFO、WARNING、ERROR、CRITICAL。
# 日志级别越高，记录的信息越少。
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 从 fastapi_app.core.config 模块中导入 get_settings 函数 ;用于获取配置
from fastapi_app.core.config import Settings, get_settings

# 日志格式
# 时间 | 日志级别 | 日志名称 | 日志消息
# %(asctime)s 记录时间，再按 datefmt 格式化
# %(levelname)-7s 日志级别，7个字符宽度，右对齐
# %(name)s 日志名称
# %(message)s 日志消息
_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
# 时间格式
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _make_formatter() -> logging.Formatter:
    """
    创建日志格式器
    :return: logging.Formatter
    """
    return logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)


def _resolve_log_dir(log_dir: str) -> Path:
    """
    解析日志目录
    :param log_dir: 日志目录
    :return: Path
    """
    # 将日志目录转换为 Path 对象
    path = Path(log_dir)
    # 如果日志目录是绝对路径，则返回 Path 对象
    # 否则返回当前工作目录下的日志目录 Path.cwd() 是当前工作目录；/ 是 pathlib 的路径拼接（不是除法）。这样无论你在 .env 里写相对目录还是绝对目录，后面都能正确创建文件。
    return path if path.is_absolute() else Path.cwd() / path


def _file_handlers(settings: Settings) -> list[logging.Handler]:
    """
    控制台之外：全量 app.log + 仅 WARNING 及以上的 error.log。
    :param settings: 设置
    :return: list[logging.Handler]
    """
    if not settings.log_dir.strip():
        # 如果日志目录为空，则返回空列表
        return []

    # 解析日志目录
    directory = _resolve_log_dir(settings.log_dir)
    # 创建日志目录
    # parents=True 中间目录不存在时一起创建。例如路径是 a/b/c，没有 a、b 也会先建好再建 c。False 时父目录缺失会报错。
    # exist_ok=True 目录已存在时不报错，而是跳过。这样写法无论目录是否存在都能正常运行。
    directory.mkdir(parents=True, exist_ok=True)

    # 创建日志处理器
    formatter = _make_formatter()
    # 创建日志处理器列表
    handlers: list[logging.Handler] = []

    # 创建日志处理器
    app_handler = RotatingFileHandler(
        # 日志文件路径
        directory / "app.log",
        # 最大文件大小
        maxBytes=settings.log_max_bytes,
        # 备份文件数量
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    # 设置日志格式
    app_handler.setFormatter(formatter)
    # 添加日志处理器
    handlers.append(app_handler)

    # 创建日志处理器
    # 线上排错优先翻这个文件；只收 WARNING / ERROR / CRITICAL。
    error_handler = RotatingFileHandler(
        directory / "error.log",
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    handlers.append(error_handler)

    return handlers


def setup_logging() -> None:
    """
    设置日志配置
    日志格式 时间 | 日志级别 | 日志名称 | 日志消息
    :return: None
    """
    settings = get_settings()
    # 根据配置文件中的 debug 设置，设置日志级别
    level = logging.DEBUG if settings.debug else logging.INFO

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(_make_formatter())

    # 输出到控制台；若配置了 log_dir，再追加滚动文件。
    logging.basicConfig(
        level=level,
        handlers=[console, *_file_handlers(settings)],
        force=True,
    )
    # 压低第三方库噪音。logging.getLogger("uvicorn.access") 获取 uvicorn 的访问日志记录器，并设置其级别为 WARNING。
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # 压低第三方库噪音。logging.getLogger("sqlalchemy.engine") 获取 SQLAlchemy 的引擎日志记录器，并根据配置文件中的 debug 设置设置其级别。
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
