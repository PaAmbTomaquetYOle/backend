"""Application entrypoint and composition root."""

from fastapi import FastAPI

from app.infrastructure.api.routers import health
from app.infrastructure.config.settings import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    return app


app = create_app()
