"""Tests for SopUpdateRequestedHandler (BE-21)."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.sop_service_interface import ISopService
from app.application.services.handlers.sop_update_requested_handler import (
    SopUpdateRequestedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import SOP_UPDATE_REQUESTED
from app.domain.exceptions.sops import SopNotFoundError


def _event(sop_id: str, **payload_overrides) -> DomainEvent:
    payload = {
        "sop_id": sop_id,
        "editor": "U1",
        "origin_channel": "C1",
        "content": "revised content",
        "tags": ["security"],
    }
    payload.update(payload_overrides)
    return DomainEvent(event_type=SOP_UPDATE_REQUESTED, payload=payload)


class TestSopUpdateRequestedHandler:
    def test_event_type(self) -> None:
        assert SopUpdateRequestedHandler().event_type == SOP_UPDATE_REQUESTED

    @pytest.mark.anyio
    async def test_handle_updates_sop(self) -> None:
        sops = AsyncMock(spec=ISopService)
        context = InboundContext(
            offboarding=AsyncMock(),
            sops=sops,
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )
        sop_id = str(uuid4())

        await SopUpdateRequestedHandler().handle(_event(sop_id), context)

        sops.update_sop.assert_awaited_once()
        args, kwargs = sops.update_sop.call_args
        assert args[0].is_equal(sop_id)
        assert kwargs["editor"].is_equal("U1")
        assert kwargs["origin_channel"].is_equal("C1")
        assert kwargs["content"] == "revised content"
        assert kwargs["tags"] == ["security"]

    @pytest.mark.anyio
    async def test_handle_defaults_content_and_tags_to_none(self) -> None:
        sops = AsyncMock(spec=ISopService)
        context = InboundContext(
            offboarding=AsyncMock(),
            sops=sops,
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )
        sop_id = str(uuid4())
        event = DomainEvent(
            event_type=SOP_UPDATE_REQUESTED,
            payload={"sop_id": sop_id, "editor": "U1", "origin_channel": "C1"},
        )

        await SopUpdateRequestedHandler().handle(event, context)

        _, kwargs = sops.update_sop.call_args
        assert kwargs["content"] is None
        assert kwargs["tags"] is None

    @pytest.mark.anyio
    async def test_drops_when_sop_not_found_instead_of_raising(self) -> None:
        sop_id = str(uuid4())
        sops = AsyncMock(spec=ISopService)
        sops.update_sop.side_effect = SopNotFoundError(sop_id)
        context = InboundContext(
            offboarding=AsyncMock(),
            sops=sops,
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await SopUpdateRequestedHandler().handle(_event(sop_id), context)  # must not raise
