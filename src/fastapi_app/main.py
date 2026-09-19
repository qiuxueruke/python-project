from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_app.api.router import api_router
from fastapi_app.core.config import get_settings
from fastapi_app.core.db import Base, engine
import fastapi_app.models  # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Demo only. Prefer Alembic migrations in production.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] skip create_all, check MySQL: {exc}")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(api_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
