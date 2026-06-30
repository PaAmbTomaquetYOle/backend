"""Application entrypoint and composition root."""

import logging
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaProducer
from fastapi import FastAPI

from app.infrastructure.adapters.events.kafka_event_publisher import KafkaEventPublisher
from app.infrastructure.adapters.events.noop_event_publisher import NoOpEventPublisher
from app.infrastructure.api.error_handlers import register_error_handlers
from app.infrastructure.api.routers import health, offboarding
from app.infrastructure.config.settings import get_settings
from app.infrastructure.persistence import (
    models as _models,  # noqa: F401 — registers SQLModel tables
)
from app.infrastructure.persistence.database import create_db_and_tables, init_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: initialize the database and Kafka producer on startup.

    Yields:
        None: Control is yielded to the application while it is running.
    """
    settings = get_settings()
    init_engine(settings.database_url)
    create_db_and_tables()

    if settings.kafka_bootstrap_servers:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id=settings.kafka_client_id,
        )
        try:
            await producer.start()
            app.state.event_publisher = KafkaEventPublisher(producer)
            logger.info("Kafka producer started")
        except Exception:
            logger.warning("Failed to start Kafka producer, using NoOpEventPublisher", exc_info=True)
            app.state.event_publisher = NoOpEventPublisher()
    else:
        app.state.event_publisher = NoOpEventPublisher()

    yield

    publisher = getattr(app.state, "event_publisher", None)
    if isinstance(publisher, KafkaEventPublisher):
        await publisher._producer.stop()
        logger.info("Kafka producer stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(offboarding.router, prefix="/api/v1")
    register_error_handlers(app)
    return app


app = create_app()
