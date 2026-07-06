"""Tests for InterviewCompletedHandler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.services.handlers.interview_completed_handler import (
    InterviewCompletedHandler,
)
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import INTERVIEW_COMPLETED


class TestInterviewCompletedHandler:
    def test_event_type(self) -> None:
        assert InterviewCompletedHandler().event_type == INTERVIEW_COMPLETED

    @pytest.mark.anyio
    async def test_handle_saves_answers_and_advances_state(self) -> None:
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()
        event = DomainEvent(
            event_type=INTERVIEW_COMPLETED,
            payload={
                "process_id": str(process_id),
                "turns": [
                    {
                        "turn_type": "question",
                        "speaker_role": "interviewer",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "content": "What are your main responsibilities?",
                        "order": 0,
                        "answer_text": "Lead the backend team",
                    },
                    {
                        "turn_type": "note",
                        "speaker_role": "interviewee",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "content": "A free-form note",
                        "order": 1,
                    },
                ],
            },
            event_id=uuid4(),
        )

        await InterviewCompletedHandler().handle(event, facade)

        facade.upsert_interview.assert_awaited_once()
        _, kwargs = facade.upsert_interview.call_args
        assert kwargs["process_id"].is_equal(process_id)
        assert len(kwargs["turns"]) == 2
        assert kwargs["turns"][0].get_turn_type() == "question"
        assert kwargs["turns"][0].answer_text == "Lead the backend team"
        assert kwargs["turns"][1].get_turn_type() == "note"

        expected_pid = kwargs["process_id"]
        facade.start_interview.assert_awaited_once_with(expected_pid)
        facade.complete_interview.assert_awaited_once_with(expected_pid)
        facade.submit_offboarding_for_review.assert_awaited_once_with(expected_pid)
