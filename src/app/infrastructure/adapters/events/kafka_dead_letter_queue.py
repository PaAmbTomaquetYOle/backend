"""Kafka implementation of IDeadLetterQueue.

Reuses the same AIOKafkaProducer instance as KafkaEventPublisher — no separate
connection is needed to park a handful of failed messages.
"""

import logging

from aiokafka import AIOKafkaProducer

from app.application.ports.dead_letter_queue import IDeadLetterQueue

logger = logging.getLogger(__name__)


class KafkaDeadLetterQueue(IDeadLetterQueue):
    """Publishes unprocessable messages to a fixed dead-letter topic."""

    def __init__(self, producer: AIOKafkaProducer, dlq_topic: str) -> None:
        self._producer = producer
        self._dlq_topic = dlq_topic

    async def send(self, raw_value: bytes, source_topic: str, error: Exception) -> None:
        """Publish the original message to the dead-letter topic with error context.

        Args:
            raw_value: The original, undeserialized message payload.
            source_topic: The topic the message was originally consumed from.
            error: The exception raised while parsing or handling the message.
        """
        headers = [
            ("source_topic", source_topic.encode("utf-8")),
            ("error", str(error).encode("utf-8")),
        ]
        try:
            await self._producer.send_and_wait(self._dlq_topic, value=raw_value, headers=headers)
        except Exception:
            logger.error(
                "Failed to publish message from %s to DLQ %s",
                source_topic,
                self._dlq_topic,
                exc_info=True,
            )
