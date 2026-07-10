"""Tests for SopCreationRequestedHandler."""

from unittest.mock import AsyncMock

import pytest

from app.application.service_interfaces.sop_service_interface import ISopService
from app.application.services.handlers.sop_creation_requested_handler import (
    SopCreationRequestedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import SOP_CREATION_REQUESTED


class TestSopCreationRequestedHandler:
    def test_event_type(self) -> None:
        assert SopCreationRequestedHandler().event_type == SOP_CREATION_REQUESTED

    @pytest.mark.anyio
    async def test_handle_creates_sop(self) -> None:
        sops = AsyncMock(spec=ISopService)
        context = InboundContext(offboarding=AsyncMock(), sops=sops, knowledge_graph=AsyncMock())
        event = DomainEvent(
            event_type=SOP_CREATION_REQUESTED,
            payload={
                "content": "How to rotate secrets",
                "author": "U1",
                "origin_channel": "C1",
                "tags": ["security"],
            },
        )

        await SopCreationRequestedHandler().handle(event, context)

        sops.create_sop.assert_awaited_once()
        _, kwargs = sops.create_sop.call_args
        assert kwargs["content"] == "How to rotate secrets"
        assert kwargs["author"].is_equal("U1")
        assert kwargs["origin_channel"].is_equal("C1")
        assert kwargs["tags"] == ["security"]

    @pytest.mark.anyio
    async def test_handle_defaults_tags_to_none(self) -> None:
        sops = AsyncMock(spec=ISopService)
        context = InboundContext(offboarding=AsyncMock(), sops=sops, knowledge_graph=AsyncMock())
        event = DomainEvent(
            event_type=SOP_CREATION_REQUESTED,
            payload={"content": "x", "author": "U1", "origin_channel": "C1"},
        )

        await SopCreationRequestedHandler().handle(event, context)

        _, kwargs = sops.create_sop.call_args
        assert kwargs["tags"] is None
