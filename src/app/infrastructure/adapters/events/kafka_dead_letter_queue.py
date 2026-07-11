"""Kafka implementation of IDeadLetterQueue.

Reuses the same AIOKafkaProducer instance as KafkaEventPublisher — no separate
connection is needed to park a handful of failed messages.
"""

import logging

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.application.observability.observed_operation import ObservedOperation
from app.application.ports.dead_letter_queue import IDeadLetterQueue
from app.application.ports.metrics import FailureKind, IMetricsPort

logger = logging.getLogger(__name__)


class DlqSendOperation(ObservedOperation[None]):
    """Sends one message to the DLQ topic, re-raising on failure instead of swallowing.

    A failed DLQ send is the critical case BE-20 exists for: the consumer
    commits the source offset right after this call, so silently swallowing
    a DLQ failure here would lose the message for good. Re-raising lets the
    caller (KafkaEventConsumer) skip the commit and let the broker redeliver
    the original message instead.
    """

    def __init__(
        self,
        metrics: IMetricsPort | None,
        producer: AIOKafkaProducer,
        dlq_topic: str,
        raw_value: bytes,
        source_topic: str,
        headers: list[tuple[str, bytes]],
    ) -> None:
        super().__init__(metrics)
        self._producer = producer
        self._dlq_topic = dlq_topic
        self._raw_value = raw_value
        self._source_topic = source_topic
        self._headers = headers

    def _expected_exceptions(self) -> tuple[type[Exception], ...]:
        return (KafkaError,)

    async def _execute(self) -> None:
        await self._producer.send_and_wait(
            self._dlq_topic, value=self._raw_value, headers=self._headers
        )

    def _failure_kind(self) -> FailureKind:
        return FailureKind.DLQ_SEND

    def _labels(self) -> dict[str, str]:
        return {"source_topic": self._source_topic, "dlq_topic": self._dlq_topic}

    def _log_failure(self, exc: Exception) -> None:
        logger.critical(
            "Failed to publish message from %s to DLQ %s — message will NOT be committed "
            "and is expected to be redelivered",
            self._source_topic,
            self._dlq_topic,
            exc_info=True,
        )

    async def _recover(self, exc: Exception) -> None:
        raise exc


class KafkaDeadLetterQueue(IDeadLetterQueue):
    """Publishes unprocessable messages to a fixed dead-letter topic."""

    def __init__(
        self,
        producer: AIOKafkaProducer,
        dlq_topic: str,
        metrics: IMetricsPort | None = None,
    ) -> None:
        self._producer = producer
        self._dlq_topic = dlq_topic
        self._metrics = metrics

    async def send(self, raw_value: bytes, source_topic: str, error: Exception) -> None:
        """Publish the original message to the dead-letter topic with error context.

        Args:
            raw_value: The original, undeserialized message payload.
            source_topic: The topic the message was originally consumed from.
            error: The exception raised while parsing or handling the message.

        Raises:
            KafkaError: If the DLQ send itself fails — propagated so the
                caller does not commit the source offset (see DlqSendOperation).
        """
        headers = [
            ("source_topic", source_topic.encode("utf-8")),
            ("error", str(error).encode("utf-8")),
        ]
        await DlqSendOperation(
            self._metrics, self._producer, self._dlq_topic, raw_value, source_topic, headers
        ).run()
