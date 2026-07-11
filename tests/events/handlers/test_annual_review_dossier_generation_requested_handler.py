"""Tests for AnnualReviewDossierGenerationRequestedHandler."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.annual_review_facade_interface import (
    IAnnualReviewServiceFacade,
)
from app.application.services.handlers.annual_review_dossier_generation_requested_handler import (
    AnnualReviewDossierGenerationRequestedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import ANNUAL_REVIEW_DOSSIER_GENERATION_REQUESTED


class TestAnnualReviewDossierGenerationRequestedHandler:
    def test_event_type(self) -> None:
        handler = AnnualReviewDossierGenerationRequestedHandler()
        assert handler.event_type == ANNUAL_REVIEW_DOSSIER_GENERATION_REQUESTED

    @pytest.mark.anyio
    async def test_handle_calls_generate_dossier(self) -> None:
        facade = AsyncMock(spec=IAnnualReviewServiceFacade)
        process_id = uuid4()
        event = DomainEvent(
            event_type=ANNUAL_REVIEW_DOSSIER_GENERATION_REQUESTED,
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
        await AnnualReviewDossierGenerationRequestedHandler().handle(event, context)

        facade.generate_dossier.assert_awaited_once()
        (pid,), _ = facade.generate_dossier.call_args
        assert pid.is_equal(process_id)
