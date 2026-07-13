"""Kafka implementation of IEventPublisher."""

import json
import logging

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.application.observability.observed_operation import ObservedOperation
from app.application.ports.event_publisher import IEventPublisher
from app.application.ports.metrics import FailureKind, IMetricsPort
from app.domain.events.base import DomainEvent
from app.infrastructure.adapters.events.topics import topic_name

logger = logging.getLogger(__name__)


class KafkaPublishOperation(ObservedOperation[None]):
    """Sends one event to Kafka, swallowing a transport failure (fire-and-forget).

    Narrowed to `KafkaError` — this is the concrete Kafka adapter, so unlike
    the application-layer `EventPublishOperation` it can afford to know the
    driver's exception hierarchy.
    """

    def __init__(
        self,
        metrics: IMetricsPort | None,
        producer: AIOKafkaProducer,
        topic: str,
        value: bytes,
        key: bytes,
        event_type: str,
    ) -> None:
        super().__init__(metrics)
        self._producer = producer
        self._topic = topic
        self._value = value
        self._key = key
        self._event_type = event_type

    def _expected_exceptions(self) -> tuple[type[Exception], ...]:
        return (KafkaError,)

    async def _execute(self) -> None:
        await self._producer.send_and_wait(self._topic, value=self._value, key=self._key)

    def _failure_kind(self) -> FailureKind:
        return FailureKind.EVENT_PUBLISH

    def _labels(self) -> dict[str, str]:
        return {"topic": self._topic, "event_type": self._event_type}

    def _log_failure(self, exc: Exception) -> None:
        logger.warning(
            "Failed to publish event %s to Kafka topic %s", self._event_type, self._topic,
            exc_info=True,
        )

    async def _recover(self, exc: Exception) -> None:
        return None


class KafkaEventPublisher(IEventPublisher):
    """Publishes domain events to Kafka topics."""

    def __init__(
        self,
        producer: AIOKafkaProducer,
        topic_prefix: str = "offboarding",
        metrics: IMetricsPort | None = None,
    ) -> None:
        self._producer = producer
        self._topic_prefix = topic_prefix
        self._metrics = metrics

    @property
    def producer(self) -> AIOKafkaProducer:
        """The underlying Kafka producer, for adapters (e.g. the DLQ) that need to reuse it."""
        return self._producer

    async def publish(self, event: DomainEvent) -> None:
        topic = topic_name(self._topic_prefix, event.event_type)
        value = json.dumps(event.to_dict()).encode("utf-8")
        key_str = event.payload.get("process_id", str(event.event_id))
        key = key_str.encode("utf-8")
        await KafkaPublishOperation(
            self._metrics, self._producer, topic, value, key, event.event_type
        ).run()

    async def publish_many(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)

    async def stop(self) -> None:
        await self._producer.stop()
