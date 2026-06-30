"""Application entrypoint and composition root."""

import logging
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaProducer
from fastapi import FastAPI
from neo4j import AsyncGraphDatabase

from app.infrastructure.adapters.events.kafka_event_publisher import KafkaEventPublisher
from app.infrastructure.adapters.events.noop_event_publisher import NoOpEventPublisher
from app.infrastructure.adapters.graph.neo4j_adapter import Neo4jAdapter
from app.infrastructure.adapters.graph.noop_graph_adapter import NoOpGraphAdapter
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
    """Manage application lifespan: initialize the database, Kafka, and Neo4j on startup.

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

    try:
        neo4j_driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        app.state.graph_db = Neo4jAdapter(neo4j_driver)
        logger.info("Neo4j driver initialized")
    except Exception:
        logger.warning("Failed to initialize Neo4j driver, using NoOpGraphAdapter", exc_info=True)
        app.state.graph_db = NoOpGraphAdapter()

    yield

    publisher = getattr(app.state, "event_publisher", None)
    if isinstance(publisher, KafkaEventPublisher):
        await publisher._producer.stop()
        logger.info("Kafka producer stopped")

    graph_db = getattr(app.state, "graph_db", None)
    if isinstance(graph_db, Neo4jAdapter):
        await graph_db._driver.close()
        logger.info("Neo4j driver stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(offboarding.router, prefix="/api/v1")
    register_error_handlers(app)
    return app


app = create_app()
