"""Tests for the Kafka event deserializer."""

import json
from uuid import uuid4

import pytest

from app.infrastructure.adapters.events.event_deserializer import (
    EventDeserializationError,
    deserialize_event,
)


class TestDeserializeEvent:
    def test_deserializes_valid_envelope(self) -> None:
        event_id = uuid4()
        raw = json.dumps({
            "event_id": str(event_id),
            "event_type": "offboarding.triggered",
            "occurred_at": "2026-07-06T10:00:00+00:00",
            "payload": {"employee_id": "U123", "manager_id": "U456"},
        }).encode("utf-8")

        event = deserialize_event(raw)

        assert event.event_id == event_id
        assert event.event_type == "offboarding.triggered"
        assert event.payload == {"employee_id": "U123", "manager_id": "U456"}

    def test_raises_on_invalid_json(self) -> None:
        with pytest.raises(EventDeserializationError):
            deserialize_event(b"not json")

    def test_raises_on_missing_field(self) -> None:
        raw = json.dumps({"event_type": "offboarding.triggered", "payload": {}}).encode("utf-8")
        with pytest.raises(EventDeserializationError):
            deserialize_event(raw)

    def test_raises_on_invalid_event_id(self) -> None:
        raw = json.dumps({
            "event_id": "not-a-uuid",
            "event_type": "offboarding.triggered",
            "occurred_at": "2026-07-06T10:00:00+00:00",
            "payload": {},
        }).encode("utf-8")
        with pytest.raises(EventDeserializationError):
            deserialize_event(raw)

    def test_raises_on_invalid_occurred_at(self) -> None:
        raw = json.dumps({
            "event_id": str(uuid4()),
            "event_type": "offboarding.triggered",
            "occurred_at": "not-a-date",
            "payload": {},
        }).encode("utf-8")
        with pytest.raises(EventDeserializationError):
            deserialize_event(raw)
