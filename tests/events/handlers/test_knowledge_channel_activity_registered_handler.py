"""Tests for KnowledgeChannelActivityRegisteredHandler."""

from unittest.mock import AsyncMock

import pytest

from app.application.service_interfaces.knowledge_graph_service_interface import (
    IKnowledgeGraphService,
)
from app.application.services.handlers.knowledge_channel_activity_registered_handler import (
    KnowledgeChannelActivityRegisteredHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import KNOWLEDGE_CHANNEL_ACTIVITY_REGISTERED


class TestKnowledgeChannelActivityRegisteredHandler:
    def test_event_type(self) -> None:
        assert (
            KnowledgeChannelActivityRegisteredHandler().event_type
            == KNOWLEDGE_CHANNEL_ACTIVITY_REGISTERED
        )

    @pytest.mark.anyio
    async def test_handle_registers_channel_activity(self) -> None:
        knowledge_graph = AsyncMock(spec=IKnowledgeGraphService)
        context = InboundContext(
            offboarding=AsyncMock(), sops=AsyncMock(), knowledge_graph=knowledge_graph
        )
        event = DomainEvent(
            event_type=KNOWLEDGE_CHANNEL_ACTIVITY_REGISTERED,
            payload={
                "person_id": "U1",
                "person_name": "Alice",
                "channel_id": "C1",
                "channel_name": "#infra",
            },
        )

        await KnowledgeChannelActivityRegisteredHandler().handle(event, context)

        knowledge_graph.register_channel_activity.assert_awaited_once_with(
            person_id="U1",
            person_name="Alice",
            channel_id="C1",
            channel_name="#infra",
        )
