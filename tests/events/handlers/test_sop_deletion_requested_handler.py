"""Tests for SopDeletionRequestedHandler (BE-21)."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.sop_service_interface import ISopService
from app.application.services.handlers.sop_deletion_requested_handler import (
    SopDeletionRequestedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import SOP_DELETION_REQUESTED
from app.domain.exceptions.sops import SopNotFoundError


def _event(sop_id: str) -> DomainEvent:
    return DomainEvent(
        event_type=SOP_DELETION_REQUESTED,
        payload={"sop_id": sop_id, "requester": "U1", "origin_channel": "C1"},
    )


class TestSopDeletionRequestedHandler:
    def test_event_type(self) -> None:
        assert SopDeletionRequestedHandler().event_type == SOP_DELETION_REQUESTED

    @pytest.mark.anyio
    async def test_handle_deletes_sop(self) -> None:
        sops = AsyncMock(spec=ISopService)
        context = InboundContext(
            offboarding=AsyncMock(),
            sops=sops,
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )
        sop_id = str(uuid4())

        await SopDeletionRequestedHandler().handle(_event(sop_id), context)

        sops.delete_sop.assert_awaited_once()
        args, kwargs = sops.delete_sop.call_args
        assert args[0].is_equal(sop_id)
        assert kwargs["requester"].is_equal("U1")
        assert kwargs["origin_channel"].is_equal("C1")

    @pytest.mark.anyio
    async def test_drops_when_sop_not_found_instead_of_raising(self) -> None:
        sop_id = str(uuid4())
        sops = AsyncMock(spec=ISopService)
        sops.delete_sop.side_effect = SopNotFoundError(sop_id)
        context = InboundContext(
            offboarding=AsyncMock(),
            sops=sops,
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await SopDeletionRequestedHandler().handle(_event(sop_id), context)  # must not raise
