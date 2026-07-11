"""Lifespan startup steps (BE-20).

Each external resource FastAPI's lifespan brings up (Kafka producer, Neo4j
driver, Kafka consumer) used to be a bare ``try/except Exception`` that only
logged a warning on failure. These `ObservedOperation` subclasses keep that
same degrade-gracefully behavior (a flaky broker/driver must not crash the
whole app at boot) but now also record a `STARTUP_DEGRADED` metric, so a
degraded deployment is visible outside the logs.

Every step keeps the base class' broad `Exception` catch on purpose: startup
failures span multiple unrelated causes (the driver's own error hierarchy,
bare socket/DNS errors raised before the driver wraps them, SSL/TLS
misconfiguration, auth failures) and every one of them must degrade to the
corresponding No-Op adapter rather than a specific per-exception recovery.
"""

import logging
from collections.abc import Callable

from aiokafka import AIOKafkaProducer
from neo4j import AsyncDriver

from app.application.observability.observed_operation import ObservedOperation
from app.application.ports.event_consumer import IEventConsumer
from app.application.ports.event_publisher import IEventPublisher
from app.application.ports.graph_database import IGraphDatabasePort
from app.application.ports.metrics import FailureKind, IMetricsPort
from app.infrastructure.adapters.events.kafka_event_publisher import KafkaEventPublisher
from app.infrastructure.adapters.events.noop_event_publisher import NoOpEventPublisher
from app.infrastructure.adapters.graph.neo4j_adapter import Neo4jAdapter
from app.infrastructure.adapters.graph.noop_graph_adapter import NoOpGraphAdapter

logger = logging.getLogger(__name__)


class KafkaProducerStartupStep(ObservedOperation[IEventPublisher]):
    """Starts the Kafka producer, degrading to NoOpEventPublisher on any failure."""

    def __init__(
        self, metrics: IMetricsPort | None, producer: AIOKafkaProducer, topic_prefix: str
    ) -> None:
        super().__init__(metrics)
        self._producer = producer
        self._topic_prefix = topic_prefix

    async def _execute(self) -> IEventPublisher:
        await self._producer.start()
        logger.info("Kafka producer started")
        return KafkaEventPublisher(
            self._producer, topic_prefix=self._topic_prefix, metrics=self._metrics
        )

    def _failure_kind(self) -> FailureKind:
        return FailureKind.STARTUP_DEGRADED

    def _labels(self) -> dict[str, str]:
        return {"component": "kafka_producer"}

    def _log_failure(self, exc: Exception) -> None:
        logger.warning("Failed to start Kafka producer, using NoOpEventPublisher", exc_info=True)

    async def _recover(self, exc: Exception) -> IEventPublisher:
        return NoOpEventPublisher()


class Neo4jStartupStep(ObservedOperation[IGraphDatabasePort]):
    """Builds the Neo4j driver/adapter and initializes its schema, degrading on failure."""

    def __init__(
        self, metrics: IMetricsPort | None, driver_factory: Callable[[], AsyncDriver]
    ) -> None:
        """Set up the step with a zero-arg factory that builds the AsyncDriver.

        Args:
            metrics: Port used to record a failure if initialization fails.
            driver_factory: Callable building the `neo4j.AsyncDriver` — kept
                lazy so driver construction itself is covered by this step's
                try/except, matching the pre-BE-20 behavior.
        """
        super().__init__(metrics)
        self._driver_factory = driver_factory

    async def _execute(self) -> IGraphDatabasePort:
        # Imported here to avoid a hard import-time dependency loop between
        # this module and the graph schema initializer.
        from app.infrastructure.adapters.graph.schema import initialize_knowledge_graph_schema

        adapter = Neo4jAdapter(self._driver_factory(), metrics=self._metrics)
        await initialize_knowledge_graph_schema(adapter)
        logger.info("Neo4j driver initialized")
        return adapter

    def _failure_kind(self) -> FailureKind:
        return FailureKind.STARTUP_DEGRADED

    def _labels(self) -> dict[str, str]:
        return {"component": "neo4j_driver"}

    def _log_failure(self, exc: Exception) -> None:
        logger.warning("Failed to initialize Neo4j driver, using NoOpGraphAdapter", exc_info=True)

    async def _recover(self, exc: Exception) -> IGraphDatabasePort:
        return NoOpGraphAdapter()


class KafkaConsumerStartupStep(ObservedOperation[IEventConsumer | None]):
    """Starts a fully-wired KafkaEventConsumer, degrading to no consumer on failure."""

    def __init__(self, metrics: IMetricsPort | None, event_consumer: IEventConsumer) -> None:
        super().__init__(metrics)
        self._event_consumer = event_consumer

    async def _execute(self) -> IEventConsumer:
        await self._event_consumer.start()
        return self._event_consumer

    def _failure_kind(self) -> FailureKind:
        return FailureKind.STARTUP_DEGRADED

    def _labels(self) -> dict[str, str]:
        return {"component": "kafka_consumer"}

    def _log_failure(self, exc: Exception) -> None:
        logger.warning("Failed to start Kafka consumer", exc_info=True)

    async def _recover(self, exc: Exception) -> None:
        return None
