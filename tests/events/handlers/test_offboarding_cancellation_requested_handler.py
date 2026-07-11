"""Tests for OffboardingCancellationRequestedHandler."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.services.handlers.offboarding_cancellation_requested_handler import (
    OffboardingCancellationRequestedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import OFFBOARDING_CANCELLATION_REQUESTED


class TestOffboardingCancellationRequestedHandler:
    def test_event_type(self) -> None:
        handler = OffboardingCancellationRequestedHandler()
        assert handler.event_type == OFFBOARDING_CANCELLATION_REQUESTED

    @pytest.mark.anyio
    async def test_handle_cancels_process(self) -> None:
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()
        event = DomainEvent(
            event_type=OFFBOARDING_CANCELLATION_REQUESTED,
            payload={"process_id": str(process_id)},
            event_id=uuid4(),
        )

        context = InboundContext(
            offboarding=facade,
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )
        await OffboardingCancellationRequestedHandler().handle(event, context)

        facade.cancel_offboarding.assert_awaited_once()
        (called_process_id,), _ = facade.cancel_offboarding.call_args
        assert called_process_id.is_equal(process_id)
