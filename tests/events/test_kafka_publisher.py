"""Tests for KafkaEventPublisher."""
import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.events.offboarding_events import OffboardingStateChanged
from app.infrastructure.adapters.events.kafka_event_publisher import KafkaEventPublisher


class TestKafkaEventPublisher:
    @pytest.mark.anyio
    async def test_publish_sends_to_correct_topic(self) -> None:
        mock_producer = AsyncMock()
        publisher = KafkaEventPublisher(mock_producer, topic_prefix="offboarding")
        event = OffboardingStateChanged(
            process_id=uuid4(),
            previous_state="not_started",
            new_state="in_progress",
            employee_id=uuid4(),
            manager_id=uuid4(),
        )
        await publisher.publish(event)
        mock_producer.send_and_wait.assert_called_once()
        call_args = mock_producer.send_and_wait.call_args
        # topic is the first positional argument
        topic = call_args[0][0]
        assert topic == "offboarding.offboarding.state_changed"

    @pytest.mark.anyio
    async def test_publish_uses_process_id_as_key(self) -> None:
        mock_producer = AsyncMock()
        publisher = KafkaEventPublisher(mock_producer)
        process_id = uuid4()
        event = OffboardingStateChanged(
            process_id=process_id,
            previous_state="not_started",
            new_state="in_progress",
            employee_id=uuid4(),
            manager_id=uuid4(),
        )
        await publisher.publish(event)
        call_args = mock_producer.send_and_wait.call_args
        key = call_args[1].get("key")
        assert key == str(process_id).encode("utf-8")

    @pytest.mark.anyio
    async def test_publish_value_is_json_encoded_event(self) -> None:
        mock_producer = AsyncMock()
        publisher = KafkaEventPublisher(mock_producer)
        process_id = uuid4()
        event = OffboardingStateChanged(
            process_id=process_id,
            previous_state="not_started",
            new_state="in_progress",
            employee_id=uuid4(),
            manager_id=uuid4(),
        )
        await publisher.publish(event)
        call_args = mock_producer.send_and_wait.call_args
        value = call_args[1].get("value")
        decoded = json.loads(value.decode("utf-8"))
        assert decoded["event_type"] == "offboarding.state_changed"
        assert decoded["payload"]["process_id"] == str(process_id)

    @pytest.mark.anyio
    async def test_publish_does_not_raise_on_kafka_error(self) -> None:
        mock_producer = AsyncMock()
        mock_producer.send_and_wait.side_effect = Exception("Kafka unavailable")
        publisher = KafkaEventPublisher(mock_producer)
        event = OffboardingStateChanged(
            process_id=uuid4(),
            previous_state="not_started",
            new_state="in_progress",
            employee_id=uuid4(),
            manager_id=uuid4(),
        )
        # Should not raise — fire and forget with logger.warning
        await publisher.publish(event)

    @pytest.mark.anyio
    async def test_publish_many_calls_publish_for_each_event(self) -> None:
        mock_producer = AsyncMock()
        publisher = KafkaEventPublisher(mock_producer)
        events = [
            OffboardingStateChanged(
                process_id=uuid4(),
                previous_state="not_started",
                new_state="in_progress",
                employee_id=uuid4(),
                manager_id=uuid4(),
            )
            for _ in range(3)
        ]
        await publisher.publish_many(events)
        assert mock_producer.send_and_wait.call_count == 3
