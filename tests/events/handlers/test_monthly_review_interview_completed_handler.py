"""Tests for MonthlyReviewInterviewCompletedHandler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.monthly_review_facade_interface import (
    IMonthlyReviewServiceFacade,
)
from app.application.services.handlers.monthly_review_interview_completed_handler import (
    MonthlyReviewInterviewCompletedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain import Interview, InterviewId, ProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import MONTHLY_REVIEW_INTERVIEW_COMPLETED
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


class TestMonthlyReviewInterviewCompletedHandler:
    def test_event_type(self) -> None:
        handler = MonthlyReviewInterviewCompletedHandler()
        assert handler.event_type == MONTHLY_REVIEW_INTERVIEW_COMPLETED

    @pytest.mark.anyio
    async def test_handle_saves_answers_and_completes_interview(self) -> None:
        facade = AsyncMock(spec=IMonthlyReviewServiceFacade)
        process_id = uuid4()
        facade.upsert_interview.return_value = (
            _interview(process_id, ScheduledInterviewState()),
            True,
        )
        event = DomainEvent(
            event_type=MONTHLY_REVIEW_INTERVIEW_COMPLETED,
            payload={
                "process_id": str(process_id),
                "turns": [
                    {
                        "turn_type": "note",
                        "speaker_role": "interviewee",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "content": "Wrapped up the monthly volunteer report",
                        "order": 0,
                    },
                ],
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
        await MonthlyReviewInterviewCompletedHandler().handle(event, context)

        facade.upsert_interview.assert_awaited_once()
        _, kwargs = facade.upsert_interview.call_args
        assert kwargs["process_id"].is_equal(process_id)
        assert len(kwargs["turns"]) == 1

        expected_pid = kwargs["process_id"]
        facade.start_interview.assert_awaited_once_with(expected_pid)
        facade.complete_interview.assert_awaited_once_with(expected_pid)

    @pytest.mark.anyio
    async def test_handle_skips_start_when_already_in_progress(self) -> None:
        facade = AsyncMock(spec=IMonthlyReviewServiceFacade)
        process_id = uuid4()
        facade.upsert_interview.return_value = (
            _interview(process_id, InProgressInterviewState()),
            False,
        )
        event = DomainEvent(
            event_type=MONTHLY_REVIEW_INTERVIEW_COMPLETED,
            payload={"process_id": str(process_id), "turns": []},
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
        await MonthlyReviewInterviewCompletedHandler().handle(event, context)

        facade.start_interview.assert_not_awaited()
        _, kwargs = facade.upsert_interview.call_args
        expected_pid = kwargs["process_id"]
        facade.complete_interview.assert_awaited_once_with(expected_pid)
