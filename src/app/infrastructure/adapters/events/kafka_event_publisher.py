"""Kafka implementation of IEventPublisher."""

import json
import logging

from aiokafka import AIOKafkaProducer

from app.application.ports.event_publisher import IEventPublisher
from app.domain.events.base import DomainEvent
from app.infrastructure.adapters.events.topics import topic_name

logger = logging.getLogger(__name__)


class KafkaEventPublisher(IEventPublisher):
    """Publishes domain events to Kafka topics."""

    def __init__(self, producer: AIOKafkaProducer, topic_prefix: str = "offboarding") -> None:
        self._producer = producer
        self._topic_prefix = topic_prefix

    async def publish(self, event: DomainEvent) -> None:
        topic = topic_name(self._topic_prefix, event.event_type)
        value = json.dumps(event.to_dict()).encode("utf-8")
        key_str = event.payload.get("process_id", str(event.event_id))
        key = key_str.encode("utf-8")
        try:
            await self._producer.send_and_wait(topic, value=value, key=key)
        except Exception:
            logger.warning("Failed to publish event %s to Kafka", event.event_type, exc_info=True)

    async def publish_many(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)
