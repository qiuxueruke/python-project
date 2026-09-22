"""静态资源挂载。"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from fastapi_app.core.config import get_settings

logger = logging.getLogger("fastapi_app.static")


def register_static_files(app: FastAPI) -> None:
    settings = get_settings()
    static_path: Path = settings.static_path
    static_path.mkdir(parents=True, exist_ok=True)
    (static_path / "uploads").mkdir(parents=True, exist_ok=True)

    mount_path = settings.static_url.rstrip("/") or "/static"
    app.mount(
        mount_path,
        StaticFiles(directory=str(static_path)),
        name="static",
    )
    logger.info("static_files mounted path=%s dir=%s", mount_path, static_path)
