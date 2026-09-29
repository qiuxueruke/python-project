"""静态资源挂载。"""
import logging
# 导入 pathlib 模块
from pathlib import Path

from fastapi import FastAPI
# 导入 StaticFiles 模块
from fastapi.staticfiles import StaticFiles

# 导入 get_settings 配置
from fastapi_app.core.config import get_settings
# 导入 logger

logger = logging.getLogger("fastapi_app.static")


def register_static_files(app: FastAPI) -> None:
    """
    注册静态文件
    :param app: FastAPI 应用
    :return: None
    """
    settings = get_settings()
    # 获取静态路径
    static_path: Path = settings.static_path
    # 创建静态路径
    static_path.mkdir(parents=True, exist_ok=True)
    # 创建上传路径
    (static_path / "uploads").mkdir(parents=True, exist_ok=True)
    # 获取挂载路径

    mount_path = settings.static_url.rstrip("/") or "/static"
    # 挂载静态文件
    app.mount(
        mount_path,
        StaticFiles(directory=str(static_path)),
        name="static",
    )
    # 打印日志
    logger.info("static_files mounted path=%s dir=%s", mount_path, static_path)
