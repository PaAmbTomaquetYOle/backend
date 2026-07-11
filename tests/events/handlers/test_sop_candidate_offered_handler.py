"""Tests for SopCandidateOfferedHandler (SA-16)."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.sop_candidate_service_interface import (
    ISopCandidateService,
)
from app.application.services.handlers.sop_candidate_offered_handler import (
    SopCandidateOfferedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import SOP_CANDIDATE_OFFERED


class TestSopCandidateOfferedHandler:
    def test_event_type(self) -> None:
        assert SopCandidateOfferedHandler().event_type == SOP_CANDIDATE_OFFERED

    @pytest.mark.anyio
    async def test_handle_records_the_offer(self) -> None:
        sop_candidates = AsyncMock(spec=ISopCandidateService)
        event = DomainEvent(
            event_type=SOP_CANDIDATE_OFFERED,
            payload={
                "channel_id": "C1",
                "author_id": "U1",
                "message_ts": "1720000000.0001",
                "content": "Rotate secrets every 90 days",
            },
            event_id=uuid4(),
        )
        context = InboundContext(
            offboarding=AsyncMock(),
            monthly_review=AsyncMock(),
            annual_review=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=sop_candidates,
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await SopCandidateOfferedHandler().handle(event, context)

        sop_candidates.record_offer.assert_awaited_once()
        _, kwargs = sop_candidates.record_offer.call_args
        assert kwargs["channel_id"].get_id() == "C1"
        assert kwargs["author_id"].get_id() == "U1"
        assert kwargs["message_ts"] == "1720000000.0001"
        assert kwargs["content"] == "Rotate secrets every 90 days"
