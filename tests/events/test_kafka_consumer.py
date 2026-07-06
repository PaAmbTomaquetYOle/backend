"""Tests for KafkaEventConsumer."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.infrastructure.adapters.events.kafka_event_consumer import KafkaEventConsumer

_PATCH_TARGET = "app.infrastructure.adapters.events.kafka_event_consumer"


def _message(value: bytes, topic: str = "slack-agent.offboarding.triggered"):
    return SimpleNamespace(value=value, topic=topic)


def _valid_envelope() -> bytes:
    return json.dumps({
        "event_id": str(uuid4()),
        "event_type": "offboarding.triggered",
        "occurred_at": "2026-07-06T10:00:00+00:00",
        "payload": {"employee_id": "U1", "manager_id": "U2"},
    }).encode("utf-8")


class TestKafkaEventConsumer:
    @pytest.mark.anyio
    async def test_process_dispatches_valid_event_and_commits(self) -> None:
        consumer, dispatcher, dlq = AsyncMock(), AsyncMock(), AsyncMock()
        event_consumer = KafkaEventConsumer(consumer, dispatcher, dlq)

        with patch(f"{_PATCH_TARGET}.build_offboarding_facade"), \
                patch(f"{_PATCH_TARGET}.get_engine"), \
                patch(f"{_PATCH_TARGET}.Session"):
            await event_consumer._process(_message(_valid_envelope()))

        dispatcher.dispatch.assert_awaited_once()
        dlq.send.assert_not_awaited()
        consumer.commit.assert_awaited_once()

    @pytest.mark.anyio
    async def test_process_routes_malformed_message_to_dlq_and_commits(self) -> None:
        consumer, dispatcher, dlq = AsyncMock(), AsyncMock(), AsyncMock()
        event_consumer = KafkaEventConsumer(consumer, dispatcher, dlq)

        await event_consumer._process(_message(b"not json"))

        dispatcher.dispatch.assert_not_awaited()
        dlq.send.assert_awaited_once()
        args, _ = dlq.send.call_args
        assert args[0] == b"not json"
        assert args[1] == "slack-agent.offboarding.triggered"
        consumer.commit.assert_awaited_once()

    @pytest.mark.anyio
    async def test_process_routes_handler_failure_to_dlq_and_commits(self) -> None:
        consumer, dispatcher, dlq = AsyncMock(), AsyncMock(), AsyncMock()
        dispatcher.dispatch.side_effect = RuntimeError("boom")
        event_consumer = KafkaEventConsumer(consumer, dispatcher, dlq)

        with patch(f"{_PATCH_TARGET}.build_offboarding_facade"), \
                patch(f"{_PATCH_TARGET}.get_engine"), \
                patch(f"{_PATCH_TARGET}.Session"):
            await event_consumer._process(_message(_valid_envelope()))

        dlq.send.assert_awaited_once()
        consumer.commit.assert_awaited_once()

    @pytest.mark.anyio
    async def test_consumer_survives_repeated_failures(self) -> None:
        """A run of malformed/failing messages never raises out of _process."""
        consumer, dispatcher, dlq = AsyncMock(), AsyncMock(), AsyncMock()
        event_consumer = KafkaEventConsumer(consumer, dispatcher, dlq)

        for _ in range(5):
            await event_consumer._process(_message(b"garbage"))

        assert dlq.send.await_count == 5
        assert consumer.commit.await_count == 5

    @pytest.mark.anyio
    async def test_start_starts_consumer_and_stop_stops_it(self) -> None:
        consumer, dispatcher, dlq = AsyncMock(), AsyncMock(), AsyncMock()
        event_consumer = KafkaEventConsumer(consumer, dispatcher, dlq)

        await event_consumer.start()
        consumer.start.assert_awaited_once()

        await event_consumer.stop()
        consumer.stop.assert_awaited_once()
