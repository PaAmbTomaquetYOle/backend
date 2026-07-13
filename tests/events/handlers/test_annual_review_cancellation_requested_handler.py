"""Tests for AnnualReviewCancellationRequestedHandler."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.annual_review_facade_interface import (
    IAnnualReviewServiceFacade,
)
from app.application.services.handlers.annual_review_cancellation_requested_handler import (
    AnnualReviewCancellationRequestedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import ANNUAL_REVIEW_CANCELLATION_REQUESTED


class TestAnnualReviewCancellationRequestedHandler:
    def test_event_type(self) -> None:
        handler = AnnualReviewCancellationRequestedHandler()
        assert handler.event_type == ANNUAL_REVIEW_CANCELLATION_REQUESTED

    @pytest.mark.anyio
    async def test_handle_cancels_process(self) -> None:
        facade = AsyncMock(spec=IAnnualReviewServiceFacade)
        process_id = uuid4()
        event = DomainEvent(
            event_type=ANNUAL_REVIEW_CANCELLATION_REQUESTED,
            payload={"process_id": str(process_id)},
            event_id=uuid4(),
        )

        context = InboundContext(
            offboarding=AsyncMock(),
            monthly_review=AsyncMock(),
            annual_review=facade,
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )
        await AnnualReviewCancellationRequestedHandler().handle(event, context)

        facade.cancel_review.assert_awaited_once()
        (called_process_id,), _ = facade.cancel_review.call_args
        assert called_process_id.is_equal(process_id)
