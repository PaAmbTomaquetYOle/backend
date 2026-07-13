"""Tests for OffboardingTriggeredHandler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.services.handlers.offboarding_triggered_handler import (
    OffboardingTriggeredHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain import EmployeeId, ManagerId, OffboardingProcess, OffboardingProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import OFFBOARDING_TRIGGERED
from app.domain.offboarding.state.not_started import NotStartedState


class TestOffboardingTriggeredHandler:
    def test_event_type(self) -> None:
        assert OffboardingTriggeredHandler().event_type == OFFBOARDING_TRIGGERED

    @pytest.mark.anyio
    async def test_handle_creates_and_starts_process(self) -> None:
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        facade.list_offboardings.return_value = []
        process = OffboardingProcess(
            process_id=OffboardingProcessId(),
            state=NotStartedState(),
            employee_id=EmployeeId("U1"),
            manager_id=ManagerId("U2"),
            created_at=datetime.now(UTC),
        )
        facade.create_offboarding.return_value = process
        event = DomainEvent(
            event_type=OFFBOARDING_TRIGGERED,
            payload={
                "employee_id": "U1",
                "manager_id": "U2",
                "employee_name": "Alice",
                "manager_name": "Bob",
            },
            event_id=uuid4(),
        )

        context = InboundContext(
            offboarding=facade,
            monthly_review=AsyncMock(),
            annual_review=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )
        await OffboardingTriggeredHandler().handle(event, context)

        facade.create_offboarding.assert_awaited_once()
        _, kwargs = facade.create_offboarding.call_args
        assert kwargs["employee_id"].is_equal("U1")
        assert kwargs["manager_id"].is_equal("U2")
        assert kwargs["employee_name"] == "Alice"
        assert kwargs["manager_name"] == "Bob"
        facade.start_offboarding.assert_awaited_once_with(process.process_id)

    @pytest.mark.anyio
    async def test_handle_reuses_existing_active_process(self) -> None:
        """Redelivery of the same event must not create a duplicate process."""
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        existing = OffboardingProcess(
            process_id=OffboardingProcessId(),
            state=NotStartedState(),
            employee_id=EmployeeId("U1"),
            manager_id=ManagerId("U2"),
            created_at=datetime.now(UTC),
        )
        facade.list_offboardings.return_value = [existing]
        event = DomainEvent(
            event_type=OFFBOARDING_TRIGGERED,
            payload={"employee_id": "U1", "manager_id": "U2"},
            event_id=uuid4(),
        )

        context = InboundContext(
            offboarding=facade,
            monthly_review=AsyncMock(),
            annual_review=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            tasks=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )
        await OffboardingTriggeredHandler().handle(event, context)

        facade.create_offboarding.assert_not_awaited()
        facade.start_offboarding.assert_awaited_once_with(existing.process_id)
