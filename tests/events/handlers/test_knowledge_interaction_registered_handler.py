"""Tests for KnowledgeInteractionRegisteredHandler."""

from unittest.mock import AsyncMock

import pytest

from app.application.service_interfaces.knowledge_graph_service_interface import (
    IKnowledgeGraphService,
)
from app.application.services.handlers.knowledge_interaction_registered_handler import (
    KnowledgeInteractionRegisteredHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import KNOWLEDGE_INTERACTION_REGISTERED


class TestKnowledgeInteractionRegisteredHandler:
    def test_event_type(self) -> None:
        assert (
            KnowledgeInteractionRegisteredHandler().event_type
            == KNOWLEDGE_INTERACTION_REGISTERED
        )

    @pytest.mark.anyio
    async def test_handle_registers_interaction(self) -> None:
        knowledge_graph = AsyncMock(spec=IKnowledgeGraphService)
        context = InboundContext(
            offboarding=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=knowledge_graph,
        )
        event = DomainEvent(
            event_type=KNOWLEDGE_INTERACTION_REGISTERED,
            payload={
                "person_id": "U1",
                "person_name": "Alice",
                "topic_name": "kubernetes",
                "interaction_type": "knows",
                "department": "SRE",
                "topic_description": "Container orchestration",
            },
        )

        await KnowledgeInteractionRegisteredHandler().handle(event, context)

        knowledge_graph.register_interaction.assert_awaited_once_with(
            person_id="U1",
            person_name="Alice",
            topic_name="kubernetes",
            interaction_type="knows",
            department="SRE",
            topic_description="Container orchestration",
        )

    @pytest.mark.anyio
    async def test_handle_defaults_optional_fields_to_none(self) -> None:
        knowledge_graph = AsyncMock(spec=IKnowledgeGraphService)
        context = InboundContext(
            offboarding=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=knowledge_graph,
        )
        event = DomainEvent(
            event_type=KNOWLEDGE_INTERACTION_REGISTERED,
            payload={
                "person_id": "U1",
                "person_name": "Alice",
                "topic_name": "kubernetes",
                "interaction_type": "answered",
            },
        )

        await KnowledgeInteractionRegisteredHandler().handle(event, context)

        _, kwargs = knowledge_graph.register_interaction.call_args
        assert kwargs["department"] is None
        assert kwargs["topic_description"] is None
