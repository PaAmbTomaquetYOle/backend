"""Tests for KafkaDeadLetterQueue (BE-20)."""

from unittest.mock import AsyncMock, Mock

import pytest
from aiokafka.errors import KafkaError

from app.infrastructure.adapters.events.kafka_dead_letter_queue import KafkaDeadLetterQueue


class TestKafkaDeadLetterQueue:
    @pytest.mark.anyio
    async def test_send_publishes_to_the_dlq_topic_with_error_context(self) -> None:
        producer = AsyncMock()
        dlq = KafkaDeadLetterQueue(producer, "offboarding.dlq")

        await dlq.send(b"raw", "slack-agent.offboarding.triggered", ValueError("bad payload"))

        producer.send_and_wait.assert_awaited_once()
        args, kwargs = producer.send_and_wait.call_args
        assert args[0] == "offboarding.dlq"
        assert kwargs["value"] == b"raw"
        header_dict = dict(kwargs["headers"])
        assert header_dict["source_topic"] == b"slack-agent.offboarding.triggered"
        assert header_dict["error"] == b"bad payload"

    @pytest.mark.anyio
    async def test_send_reraises_and_records_metric_when_dlq_send_fails(self) -> None:
        """The critical BE-20 case: a failed DLQ send must propagate, never be swallowed."""
        producer = AsyncMock()
        producer.send_and_wait.side_effect = KafkaError("DLQ unavailable")
        metrics = Mock()
        dlq = KafkaDeadLetterQueue(producer, "offboarding.dlq", metrics=metrics)

        with pytest.raises(KafkaError):
            await dlq.send(b"raw", "slack-agent.offboarding.triggered", ValueError("bad payload"))

        metrics.increment_failure.assert_called_once()

    @pytest.mark.anyio
    async def test_send_does_not_raise_when_metrics_is_none(self) -> None:
        producer = AsyncMock()
        producer.send_and_wait.side_effect = KafkaError("DLQ unavailable")
        dlq = KafkaDeadLetterQueue(producer, "offboarding.dlq")

        with pytest.raises(KafkaError):
            await dlq.send(b"raw", "slack-agent.offboarding.triggered", ValueError("bad"))
