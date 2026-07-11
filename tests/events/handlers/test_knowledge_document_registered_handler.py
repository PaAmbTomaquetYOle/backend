"""Tests for KnowledgeDocumentRegisteredHandler."""

from unittest.mock import AsyncMock

import pytest

from app.application.service_interfaces.knowledge_graph_service_interface import (
    IKnowledgeGraphService,
)
from app.application.services.handlers.knowledge_document_registered_handler import (
    KnowledgeDocumentRegisteredHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import KNOWLEDGE_DOCUMENT_REGISTERED


class TestKnowledgeDocumentRegisteredHandler:
    def test_event_type(self) -> None:
        assert KnowledgeDocumentRegisteredHandler().event_type == KNOWLEDGE_DOCUMENT_REGISTERED

    @pytest.mark.anyio
    async def test_handle_registers_document(self) -> None:
        knowledge_graph = AsyncMock(spec=IKnowledgeGraphService)
        context = InboundContext(
            offboarding=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=knowledge_graph,
        )
        event = DomainEvent(
            event_type=KNOWLEDGE_DOCUMENT_REGISTERED,
            payload={
                "document_id": "D1",
                "title": "Kubernetes Runbook",
                "author_id": "U1",
                "author_name": "Alice",
                "topics": ["kubernetes", "sre"],
                "url": "https://example.com/runbook",
                "source": "confluence",
            },
        )

        await KnowledgeDocumentRegisteredHandler().handle(event, context)

        knowledge_graph.register_document.assert_awaited_once_with(
            document_id="D1",
            title="Kubernetes Runbook",
            author_id="U1",
            author_name="Alice",
            topics=["kubernetes", "sre"],
            url="https://example.com/runbook",
            source="confluence",
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
            event_type=KNOWLEDGE_DOCUMENT_REGISTERED,
            payload={
                "document_id": "D1",
                "title": "Kubernetes Runbook",
                "author_id": "U1",
                "author_name": "Alice",
                "topics": [],
            },
        )

        await KnowledgeDocumentRegisteredHandler().handle(event, context)

        _, kwargs = knowledge_graph.register_document.call_args
        assert kwargs["url"] is None
        assert kwargs["source"] is None
