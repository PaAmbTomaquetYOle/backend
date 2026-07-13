"""Tests for AnnualReviewInterviewCompletedHandler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.annual_review_facade_interface import (
    IAnnualReviewServiceFacade,
)
from app.application.services.handlers.annual_review_interview_completed_handler import (
    AnnualReviewInterviewCompletedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain import Interview, InterviewId, ProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import ANNUAL_REVIEW_INTERVIEW_COMPLETED
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


class TestAnnualReviewInterviewCompletedHandler:
    def test_event_type(self) -> None:
        handler = AnnualReviewInterviewCompletedHandler()
        assert handler.event_type == ANNUAL_REVIEW_INTERVIEW_COMPLETED

    @pytest.mark.anyio
    async def test_handle_saves_answers_and_advances_state(self) -> None:
        facade = AsyncMock(spec=IAnnualReviewServiceFacade)
        process_id = uuid4()
        facade.upsert_interview.return_value = (
            _interview(process_id, ScheduledInterviewState()),
            True,
        )
        event = DomainEvent(
            event_type=ANNUAL_REVIEW_INTERVIEW_COMPLETED,
            payload={
                "process_id": str(process_id),
                "turns": [
                    {
                        "turn_type": "question",
                        "speaker_role": "interviewer",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "content": "What knowledge should be documented this year?",
                        "order": 0,
                        "answer_text": "The deployment runbook",
                    },
                ],
            },
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
        await AnnualReviewInterviewCompletedHandler().handle(event, context)

        facade.upsert_interview.assert_awaited_once()
        _, kwargs = facade.upsert_interview.call_args
        assert kwargs["process_id"].is_equal(process_id)
        assert len(kwargs["turns"]) == 1

        expected_pid = kwargs["process_id"]
        facade.start_interview.assert_awaited_once_with(expected_pid)
        facade.complete_interview.assert_awaited_once_with(expected_pid)
        facade.submit_review_for_review.assert_awaited_once_with(expected_pid)

    @pytest.mark.anyio
    async def test_handle_skips_start_when_already_in_progress(self) -> None:
        facade = AsyncMock(spec=IAnnualReviewServiceFacade)
        process_id = uuid4()
        facade.upsert_interview.return_value = (
            _interview(process_id, InProgressInterviewState()),
            False,
        )
        event = DomainEvent(
            event_type=ANNUAL_REVIEW_INTERVIEW_COMPLETED,
            payload={"process_id": str(process_id), "turns": []},
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
        await AnnualReviewInterviewCompletedHandler().handle(event, context)

        facade.start_interview.assert_not_awaited()
        _, kwargs = facade.upsert_interview.call_args
        expected_pid = kwargs["process_id"]
        facade.complete_interview.assert_awaited_once_with(expected_pid)
        facade.submit_review_for_review.assert_awaited_once_with(expected_pid)
