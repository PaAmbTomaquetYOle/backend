"""Tests for MonthlyReviewDossierGenerationRequestedHandler."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.monthly_review_facade_interface import (
    IMonthlyReviewServiceFacade,
)
from app.application.services.handlers.monthly_review_dossier_generation_requested_handler import (
    MonthlyReviewDossierGenerationRequestedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import MONTHLY_REVIEW_DOSSIER_GENERATION_REQUESTED


class TestMonthlyReviewDossierGenerationRequestedHandler:
    def test_event_type(self) -> None:
        handler = MonthlyReviewDossierGenerationRequestedHandler()
        assert handler.event_type == MONTHLY_REVIEW_DOSSIER_GENERATION_REQUESTED

    @pytest.mark.anyio
    async def test_handle_calls_generate_dossier(self) -> None:
        facade = AsyncMock(spec=IMonthlyReviewServiceFacade)
        process_id = uuid4()
        event = DomainEvent(
            event_type=MONTHLY_REVIEW_DOSSIER_GENERATION_REQUESTED,
            payload={"process_id": str(process_id)},
            event_id=uuid4(),
        )

        context = InboundContext(
            offboarding=AsyncMock(),
            monthly_review=facade,
            annual_review=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )
        await MonthlyReviewDossierGenerationRequestedHandler().handle(event, context)

        facade.generate_dossier.assert_awaited_once()
        (pid,), _ = facade.generate_dossier.call_args
        assert pid.is_equal(process_id)
