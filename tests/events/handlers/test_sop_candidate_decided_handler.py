"""Tests for SopCandidateDecidedHandler (SA-16)."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.sop_candidate_service_interface import (
    ISopCandidateService,
)
from app.application.services.handlers.sop_candidate_decided_handler import (
    SopCandidateDecidedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import SOP_CANDIDATE_DECIDED
from app.domain.exceptions.sops import (
    InvalidSopCandidateTransitionError,
    SopCandidateNotFoundError,
)


def _event(accepted: bool) -> DomainEvent:
    return DomainEvent(
        event_type=SOP_CANDIDATE_DECIDED,
        payload={"channel_id": "C1", "message_ts": "1720000000.0001", "accepted": accepted},
        event_id=uuid4(),
    )


class TestSopCandidateDecidedHandler:
    def test_event_type(self) -> None:
        assert SopCandidateDecidedHandler().event_type == SOP_CANDIDATE_DECIDED

    @pytest.mark.anyio
    async def test_handle_records_an_accepted_decision(self) -> None:
        sop_candidates = AsyncMock(spec=ISopCandidateService)
        context = InboundContext(
            offboarding=AsyncMock(),
            monthly_review=AsyncMock(),
            annual_review=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=sop_candidates,
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await SopCandidateDecidedHandler().handle(_event(accepted=True), context)

        sop_candidates.record_decision.assert_awaited_once()
        _, kwargs = sop_candidates.record_decision.call_args
        assert kwargs["channel_id"].get_id() == "C1"
        assert kwargs["message_ts"] == "1720000000.0001"
        assert kwargs["accepted"] is True

    @pytest.mark.anyio
    async def test_drops_when_candidate_not_found_instead_of_raising(self) -> None:
        sop_candidates = AsyncMock(spec=ISopCandidateService)
        sop_candidates.record_decision.side_effect = SopCandidateNotFoundError("C1", "ts")
        context = InboundContext(
            offboarding=AsyncMock(),
            monthly_review=AsyncMock(),
            annual_review=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=sop_candidates,
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await SopCandidateDecidedHandler().handle(_event(accepted=False), context)  # must not raise

    @pytest.mark.anyio
    async def test_drops_when_already_decided_instead_of_raising(self) -> None:
        sop_candidates = AsyncMock(spec=ISopCandidateService)
        sop_candidates.record_decision.side_effect = InvalidSopCandidateTransitionError("accepted")
        context = InboundContext(
            offboarding=AsyncMock(),
            monthly_review=AsyncMock(),
            annual_review=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=sop_candidates,
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await SopCandidateDecidedHandler().handle(_event(accepted=True), context)  # must not raise
