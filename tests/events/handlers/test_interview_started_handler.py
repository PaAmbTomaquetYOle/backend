"""Tests for InterviewStartedHandler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.services.handlers.interview_started_handler import (
    InterviewStartedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain import Interview, InterviewId, ProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import INTERVIEW_STARTED
from app.domain.interview.state.in_progress import InProgressInterviewState
from app.domain.interview.state.scheduled import ScheduledInterviewState


def _interview(process_id, state) -> Interview:
    return Interview(
        interview_id=InterviewId(),
        process_id=ProcessId(process_id),
        state=state,
        scheduled_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )


class TestInterviewStartedHandler:
    def test_event_type(self) -> None:
        assert InterviewStartedHandler().event_type == INTERVIEW_STARTED

    @pytest.mark.anyio
    async def test_handle_creates_and_starts_new_interview(self) -> None:
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()
        interview = _interview(process_id, ScheduledInterviewState())
        facade.upsert_interview.return_value = (interview, True)

        event = DomainEvent(
            event_type=INTERVIEW_STARTED,
            payload={"process_id": str(process_id), "employee_id": "U1"},
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

        await InterviewStartedHandler().handle(event, context)

        facade.upsert_interview.assert_awaited_once()
        _, kwargs = facade.upsert_interview.call_args
        assert kwargs["process_id"].is_equal(process_id)
        assert kwargs["scheduled_at"] == event.occurred_at

        facade.start_interview.assert_awaited_once_with(kwargs["process_id"])

    @pytest.mark.anyio
    async def test_handle_is_idempotent_when_already_in_progress(self) -> None:
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()
        interview = _interview(process_id, InProgressInterviewState())
        facade.upsert_interview.return_value = (interview, False)

        event = DomainEvent(
            event_type=INTERVIEW_STARTED,
            payload={"process_id": str(process_id), "employee_id": "U1"},
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

        await InterviewStartedHandler().handle(event, context)

        facade.upsert_interview.assert_awaited_once()
        facade.start_interview.assert_not_awaited()
