"""Tests for MonthlyReviewTriggeredHandler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.monthly_review_facade_interface import (
    IMonthlyReviewServiceFacade,
)
from app.application.services.handlers.monthly_review_triggered_handler import (
    MonthlyReviewTriggeredHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain import EmployeeId, ManagerId, MonthlyReviewProcess, MonthlyReviewProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import MONTHLY_REVIEW_TRIGGERED
from app.domain.monthly_review.state.not_started import NotStartedState


class TestMonthlyReviewTriggeredHandler:
    def test_event_type(self) -> None:
        assert MonthlyReviewTriggeredHandler().event_type == MONTHLY_REVIEW_TRIGGERED

    @pytest.mark.anyio
    async def test_handle_creates_and_starts_process(self) -> None:
        facade = AsyncMock(spec=IMonthlyReviewServiceFacade)
        facade.list_reviews.return_value = []
        process = MonthlyReviewProcess(
            process_id=MonthlyReviewProcessId(),
            state=NotStartedState(),
            employee_id=EmployeeId("U1"),
            manager_id=ManagerId("U2"),
            created_at=datetime.now(UTC),
        )
        facade.create_review.return_value = process
        event = DomainEvent(
            event_type=MONTHLY_REVIEW_TRIGGERED,
            payload={
                "employee_id": "U1",
                "manager_id": "U2",
                "employee_name": "Alice",
                "manager_name": "Bob",
            },
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
        await MonthlyReviewTriggeredHandler().handle(event, context)

        facade.create_review.assert_awaited_once()
        _, kwargs = facade.create_review.call_args
        assert kwargs["employee_id"].is_equal("U1")
        assert kwargs["manager_id"].is_equal("U2")
        assert kwargs["employee_name"] == "Alice"
        assert kwargs["manager_name"] == "Bob"
        facade.start_review.assert_awaited_once_with(process.process_id)

    @pytest.mark.anyio
    async def test_handle_reuses_existing_active_process(self) -> None:
        """Redelivery of the same event must not create a duplicate process."""
        facade = AsyncMock(spec=IMonthlyReviewServiceFacade)
        existing = MonthlyReviewProcess(
            process_id=MonthlyReviewProcessId(),
            state=NotStartedState(),
            employee_id=EmployeeId("U1"),
            manager_id=ManagerId("U2"),
            created_at=datetime.now(UTC),
        )
        facade.list_reviews.return_value = [existing]
        event = DomainEvent(
            event_type=MONTHLY_REVIEW_TRIGGERED,
            payload={"employee_id": "U1", "manager_id": "U2"},
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
        await MonthlyReviewTriggeredHandler().handle(event, context)

        facade.create_review.assert_not_awaited()
        facade.start_review.assert_awaited_once_with(existing.process_id)
