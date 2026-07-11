"""Application entrypoint and composition root."""

import asyncio
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
    AnnualReviewCancellationRequestedHandler,
    AnnualReviewDossierGenerationRequestedHandler,
    AnnualReviewInterviewCompletedHandler,
    AnnualReviewTriggeredHandler,
    DossierGenerationRequestedHandler,
    InterviewCompletedHandler,
    InterviewStartedHandler,
    InterviewTurnRecordedHandler,
    KnowledgeChannelActivityRegisteredHandler,
    KnowledgeDocumentRegisteredHandler,
    KnowledgeInteractionRegisteredHandler,
    MonthlyReviewCancellationRequestedHandler,
    MonthlyReviewDossierGenerationRequestedHandler,
    MonthlyReviewInterviewCompletedHandler,
    MonthlyReviewTriggeredHandler,
    OffboardingCancellationRequestedHandler,
    OffboardingTasksExtractedHandler,
    OffboardingTriggeredHandler,
    SopCandidateDecidedHandler,
    SopCandidateOfferedHandler,
    SopCreationRequestedHandler,
    SopDeletionRequestedHandler,
    SopUpdateRequestedHandler,
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
from app.infrastructure.adapters.metrics.noop_metrics import NoOpMetrics
from app.infrastructure.adapters.metrics.prometheus_metrics import PrometheusMetricsAdapter
from app.infrastructure.api.error_handlers import register_error_handlers
from app.infrastructure.api.rate_limiter import limiter
from app.infrastructure.api.routers import (
    auth,
    dossier,
    health,
    knowledge_graph,
    offboarding,
    sop_candidates,
    sops,
)
from app.infrastructure.api.routers import (
    metrics as metrics_router,
)
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.persistence import (
    models as _models,  # noqa: F401 — registers SQLModel tables
)
from app.infrastructure.persistence.database import get_engine, init_engine
from app.infrastructure.scheduling import ReviewScheduler
from app.infrastructure.startup_steps import (
    KafkaConsumerStartupStep,
    KafkaProducerStartupStep,
    Neo4jStartupStep,
)

logger = logging.getLogger(__name__)


async def _initialize_neo4j_schema(graph_db: Neo4jAdapter) -> None:
    """Initialize the Neo4j schema in the background without blocking startup."""

    try:
        await initialize_knowledge_graph_schema(graph_db)
        logger.info("Neo4j schema initialized")
    except Exception:
        logger.warning("Failed to initialize Neo4j schema", exc_info=True)


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

    app.state.metrics = PrometheusMetricsAdapter() if settings.metrics_enabled else NoOpMetrics()
    metrics = app.state.metrics

    if settings.kafka_bootstrap_servers:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id=settings.kafka_client_id,
            **_kafka_connection_kwargs(settings),
        )
        app.state.event_publisher = await KafkaProducerStartupStep(
            metrics, producer, settings.kafka_topic_prefix
        ).run()
    else:
        app.state.event_publisher = NoOpEventPublisher()

    fake_dossier_generator = FakeDossierGenerator()
    if settings.dossier_llm_enabled:
        app.state.dossier_generator = LLMDossierGenerator(
            mcp_server_url=settings.mcp_server_url,
            fallback=fake_dossier_generator,
            timeout_seconds=settings.dossier_llm_timeout_seconds,
            metrics=metrics,
        )
        logger.info("Using LLMDossierGenerator (mcp_server=%s)", settings.mcp_server_url)
    else:
        app.state.dossier_generator = fake_dossier_generator

    app.state.review_scheduler = None
    if settings.review_scheduling_enabled:
        app.state.review_scheduler = ReviewScheduler(
            hour_utc=settings.review_scheduling_hour_utc,
            event_publisher=app.state.event_publisher,
            dossier_generator=app.state.dossier_generator,
            metrics=metrics,
        )
        app.state.review_scheduler.start()

    app.state.graph_db = await Neo4jStartupStep(
        metrics,
        lambda: AsyncGraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        ),
    ).run()

    app.state.event_consumer = None
    if isinstance(app.state.event_publisher, KafkaEventPublisher):
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
            app.state.event_publisher.producer, settings.kafka_dlq_topic, metrics=metrics
        )
        dispatcher = InboundEventDispatcher([
            OffboardingTriggeredHandler(),
            OffboardingCancellationRequestedHandler(),
            InterviewStartedHandler(),
            InterviewCompletedHandler(),
            InterviewTurnRecordedHandler(),
            OffboardingTasksExtractedHandler(),
            DossierGenerationRequestedHandler(),
            SopCreationRequestedHandler(),
            SopUpdateRequestedHandler(),
            SopDeletionRequestedHandler(),
            SopCandidateOfferedHandler(),
            SopCandidateDecidedHandler(),
            KnowledgeInteractionRegisteredHandler(),
            KnowledgeDocumentRegisteredHandler(),
            KnowledgeChannelActivityRegisteredHandler(),
            MonthlyReviewTriggeredHandler(),
            MonthlyReviewCancellationRequestedHandler(),
            MonthlyReviewInterviewCompletedHandler(),
            MonthlyReviewDossierGenerationRequestedHandler(),
            AnnualReviewTriggeredHandler(),
            AnnualReviewCancellationRequestedHandler(),
            AnnualReviewInterviewCompletedHandler(),
            AnnualReviewDossierGenerationRequestedHandler(),
        ])
        event_consumer = KafkaEventConsumer(
            consumer=kafka_consumer,
            dispatcher=dispatcher,
            dead_letter_queue=dead_letter_queue,
            graph_db=app.state.graph_db,
            event_publisher=app.state.event_publisher,
            dossier_generator=app.state.dossier_generator,
            metrics=metrics,
        )
        app.state.event_consumer = await KafkaConsumerStartupStep(metrics, event_consumer).run()
        if app.state.event_consumer is not None:
            logger.info("Kafka consumer started, subscribed to %s", inbound_topics)

    yield

    review_scheduler = getattr(app.state, "review_scheduler", None)
    if review_scheduler is not None:
        review_scheduler.stop()

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
    app.include_router(sop_candidates.router, prefix="/api/v1")
    app.include_router(knowledge_graph.router, prefix="/api/v1")
    if settings.metrics_enabled:
        app.include_router(metrics_router.router, prefix="/api/v1")
    register_error_handlers(app)
    return app


app = create_app()
