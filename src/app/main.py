"""Application entrypoint and composition root."""

import logging
import ssl
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI
from neo4j import AsyncGraphDatabase
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.application.services.handlers import (
    DossierGenerationRequestedHandler,
    InterviewCompletedHandler,
    InterviewStartedHandler,
    InterviewTurnRecordedHandler,
    KnowledgeChannelActivityRegisteredHandler,
    KnowledgeDocumentRegisteredHandler,
    KnowledgeInteractionRegisteredHandler,
    OffboardingCancellationRequestedHandler,
    OffboardingTriggeredHandler,
    SopCreationRequestedHandler,
)
from app.application.services.inbound_event_dispatcher import InboundEventDispatcher
from app.domain.events.inbound_events import INBOUND_EVENT_TYPES
from app.infrastructure.adapters.ai.fake_dossier_generator import FakeDossierGenerator
from app.infrastructure.adapters.ai.llm_dossier_generator import LLMDossierGenerator
from app.infrastructure.adapters.events.kafka_dead_letter_queue import KafkaDeadLetterQueue
from app.infrastructure.adapters.events.kafka_event_consumer import KafkaEventConsumer
from app.infrastructure.adapters.events.kafka_event_publisher import KafkaEventPublisher
from app.infrastructure.adapters.events.noop_event_publisher import NoOpEventPublisher
from app.infrastructure.adapters.events.topics import topic_name
from app.infrastructure.adapters.graph.neo4j_adapter import Neo4jAdapter
from app.infrastructure.adapters.graph.noop_graph_adapter import NoOpGraphAdapter
from app.infrastructure.adapters.graph.schema import initialize_knowledge_graph_schema
from app.infrastructure.api.error_handlers import register_error_handlers
from app.infrastructure.api.rate_limiter import limiter
from app.infrastructure.api.routers import auth, dossier, health, knowledge_graph, offboarding, sops
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.persistence import (
    models as _models,  # noqa: F401 — registers SQLModel tables
)
from app.infrastructure.persistence.database import get_engine, init_engine

logger = logging.getLogger(__name__)


def _kafka_connection_kwargs(settings: Settings) -> dict:
    """Build the security-related kwargs shared by the Kafka producer and consumer.

    Defaults to PLAINTEXT (no extra kwargs) so local dev/tests are unaffected.
    When SASL is configured, adds SASL credentials; when SASL_SSL/SSL is
    configured, additionally builds a TLS context from the configured CA file.

    Args:
        settings: Application settings holding the Kafka security configuration.

    Returns:
        dict: Keyword arguments to merge into the producer/consumer constructor.
    """
    kwargs: dict = {"security_protocol": settings.kafka_security_protocol}
    protocol = settings.kafka_security_protocol.upper()
    if protocol.startswith("SASL"):
        kwargs["sasl_mechanism"] = settings.kafka_sasl_mechanism
        kwargs["sasl_plain_username"] = settings.kafka_sasl_username
        kwargs["sasl_plain_password"] = settings.kafka_sasl_password
    if protocol.endswith("SSL"):
        kwargs["ssl_context"] = ssl.create_default_context(
            cafile=settings.kafka_ssl_cafile or None
        )
    return kwargs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: initialize the database, Kafka, and Neo4j on startup.

    Yields:
        None: Control is yielded to the application while it is running.
    """
    settings = get_settings()
    init_engine(settings.database_url)

    if settings.kafka_bootstrap_servers:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id=settings.kafka_client_id,
            **_kafka_connection_kwargs(settings),
        )
        try:
            await producer.start()
            app.state.event_publisher = KafkaEventPublisher(
                producer, topic_prefix=settings.kafka_topic_prefix
            )
            logger.info("Kafka producer started")
        except Exception:
            logger.warning(
                "Failed to start Kafka producer, using NoOpEventPublisher", exc_info=True
            )
            app.state.event_publisher = NoOpEventPublisher()
    else:
        app.state.event_publisher = NoOpEventPublisher()

    fake_dossier_generator = FakeDossierGenerator()
    if settings.dossier_llm_enabled:
        app.state.dossier_generator = LLMDossierGenerator(
            mcp_server_url=settings.mcp_server_url,
            fallback=fake_dossier_generator,
            timeout_seconds=settings.dossier_llm_timeout_seconds,
        )
        logger.info("Using LLMDossierGenerator (mcp_server=%s)", settings.mcp_server_url)
    else:
        app.state.dossier_generator = fake_dossier_generator
    try:
        neo4j_driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        app.state.graph_db = Neo4jAdapter(neo4j_driver)
        await initialize_knowledge_graph_schema(app.state.graph_db)
        logger.info("Neo4j driver initialized")
    except Exception:
        logger.warning("Failed to initialize Neo4j driver, using NoOpGraphAdapter", exc_info=True)
        app.state.graph_db = NoOpGraphAdapter()

    app.state.event_consumer = None
    if isinstance(app.state.event_publisher, KafkaEventPublisher):
        try:
            inbound_topics = [
                topic_name(settings.kafka_inbound_topic_prefix, event_type)
                for event_type in INBOUND_EVENT_TYPES
            ]
            kafka_consumer = AIOKafkaConsumer(
                *inbound_topics,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                client_id=settings.kafka_client_id,
                group_id=settings.kafka_consumer_group_id,
                enable_auto_commit=False,
                **_kafka_connection_kwargs(settings),
            )
            dead_letter_queue = KafkaDeadLetterQueue(
                app.state.event_publisher.producer, settings.kafka_dlq_topic
            )
            dispatcher = InboundEventDispatcher([
                OffboardingTriggeredHandler(),
                OffboardingCancellationRequestedHandler(),
                InterviewStartedHandler(),
                InterviewCompletedHandler(),
                InterviewTurnRecordedHandler(),
                DossierGenerationRequestedHandler(),
                SopCreationRequestedHandler(),
                KnowledgeInteractionRegisteredHandler(),
                KnowledgeDocumentRegisteredHandler(),
                KnowledgeChannelActivityRegisteredHandler(),
            ])
            event_consumer = KafkaEventConsumer(
                consumer=kafka_consumer,
                dispatcher=dispatcher,
                dead_letter_queue=dead_letter_queue,
                graph_db=app.state.graph_db,
                event_publisher=app.state.event_publisher,
                dossier_generator=app.state.dossier_generator,
            )
            await event_consumer.start()
            app.state.event_consumer = event_consumer
            logger.info("Kafka consumer started, subscribed to %s", inbound_topics)
        except Exception:
            logger.warning("Failed to start Kafka consumer", exc_info=True)
            app.state.event_consumer = None

    yield

    event_consumer = getattr(app.state, "event_consumer", None)
    if event_consumer is not None:
        await event_consumer.stop()
        logger.info("Kafka consumer stopped")

    publisher = getattr(app.state, "event_publisher", None)
    if isinstance(publisher, KafkaEventPublisher):
        await publisher.stop()
        logger.info("Kafka producer stopped")

    graph_db = getattr(app.state, "graph_db", None)
    if isinstance(graph_db, Neo4jAdapter):
        await graph_db._driver.close()
        logger.info("Neo4j driver stopped")

    await get_engine().dispose()
    logger.info("Database engine disposed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(offboarding.router, prefix="/api/v1")
    app.include_router(dossier.router, prefix="/api/v1")
    app.include_router(sops.router, prefix="/api/v1")
    app.include_router(knowledge_graph.router, prefix="/api/v1")
    register_error_handlers(app)
    return app


app = create_app()
