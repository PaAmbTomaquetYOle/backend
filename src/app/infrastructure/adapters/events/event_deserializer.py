"""Deserializes raw Kafka message bytes into a DomainEvent.

Reverses DomainEvent.to_dict() (see app.domain.events.base). Raises on any
malformed input so the caller can route the message to the dead-letter queue
instead of crashing the consumer loop.
"""

import json
from datetime import datetime
from uuid import UUID

from app.domain.events.base import DomainEvent


class EventDeserializationError(ValueError):
    """Raised when a raw Kafka message cannot be parsed into a DomainEvent."""


def deserialize_event(raw_value: bytes) -> DomainEvent:
    """Parse a raw Kafka message value into a DomainEvent.

    Args:
        raw_value: The raw UTF-8 JSON-encoded message value.

    Returns:
        The reconstructed DomainEvent.

    Raises:
        EventDeserializationError: If the payload is not valid JSON, is missing
            required envelope fields, or has fields of the wrong shape.
    """
    try:
        raw = json.loads(raw_value.decode("utf-8"))
        return DomainEvent(
            event_type=raw["event_type"],
            payload=raw["payload"],
            event_id=UUID(raw["event_id"]),
            occurred_at=datetime.fromisoformat(raw["occurred_at"]),
        )
    except Exception as exc:
        raise EventDeserializationError(f"Malformed event envelope: {exc}") from exc
