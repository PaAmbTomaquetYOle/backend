"""Application entrypoint and composition root."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.api.error_handlers import register_error_handlers
from app.infrastructure.api.routers import health, offboarding
from app.infrastructure.config.settings import get_settings
from app.infrastructure.persistence import (
    models as _models,  # noqa: F401 — registers SQLModel tables
)
from app.infrastructure.persistence.database import create_db_and_tables, init_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: initialize the database on startup.

    Yields:
        None: Control is yielded to the application while it is running.
    """
    settings = get_settings()
    init_engine(settings.database_url)
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(offboarding.router, prefix="/api/v1")
    register_error_handlers(app)
    return app


app = create_app()
