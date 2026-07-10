"""Tests for DossierGenerationRequestedHandler."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.services.handlers.dossier_generation_requested_handler import (
    DossierGenerationRequestedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import DOSSIER_GENERATION_REQUESTED


class TestDossierGenerationRequestedHandler:
    def test_event_type(self) -> None:
        assert DossierGenerationRequestedHandler().event_type == DOSSIER_GENERATION_REQUESTED

    @pytest.mark.anyio
    async def test_handle_calls_generate_dossier(self) -> None:
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()
        event = DomainEvent(
            event_type=DOSSIER_GENERATION_REQUESTED,
            payload={"process_id": str(process_id)},
            event_id=uuid4(),
        )

        context = InboundContext(offboarding=facade, sops=AsyncMock(), knowledge_graph=AsyncMock())
        await DossierGenerationRequestedHandler().handle(event, context)

        facade.generate_dossier.assert_awaited_once()
        (pid,), _ = facade.generate_dossier.call_args
        assert pid.is_equal(process_id)
