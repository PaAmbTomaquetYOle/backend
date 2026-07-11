"""Tests for InterviewTurnRecordedHandler (SA-16)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.services.handlers.interview_turn_recorded_handler import (
    InterviewTurnRecordedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain import Interview, InterviewId, InterviewNote, ProcessId, SpeakerRoleEnum
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import INTERVIEW_TURN_RECORDED
from app.domain.exceptions.interview import InterviewNotFoundError
from app.domain.interview.state.completed import CompletedInterviewState
from app.domain.interview.state.in_progress import InProgressInterviewState
from app.domain.interview.state.scheduled import ScheduledInterviewState


def _interview(process_id, state, turns=None) -> Interview:
    return Interview(
        interview_id=InterviewId(),
        process_id=ProcessId(process_id),
        state=state,
        scheduled_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        turns=turns,
    )


def _turn(order: int) -> InterviewNote:
    return InterviewNote(
        speaker_role=SpeakerRoleEnum.INTERVIEWEE,
        timestamp=datetime.now(UTC),
        content=f"turn {order}",
        order=order,
    )


def _event(process_id, orders: list[int]) -> DomainEvent:
    return DomainEvent(
        event_type=INTERVIEW_TURN_RECORDED,
        payload={
            "process_id": str(process_id),
            "turns": [
                {
                    "turn_type": "note",
                    "speaker_role": "interviewee",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "content": f"turn {order}",
                    "order": order,
                }
                for order in orders
            ],
        },
        event_id=uuid4(),
    )


class TestInterviewTurnRecordedHandler:
    def test_event_type(self) -> None:
        assert InterviewTurnRecordedHandler().event_type == INTERVIEW_TURN_RECORDED

    @pytest.mark.anyio
    async def test_creates_and_starts_the_interview_when_none_exists_yet(self) -> None:
        """Kafka delivery is unordered: turn_recorded may arrive before interview.started."""
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()
        facade.get_interview.side_effect = InterviewNotFoundError("not found")
        created_interview = _interview(process_id, ScheduledInterviewState())
        facade.upsert_interview.return_value = (created_interview, True)
        facade.start_interview.return_value = _interview(process_id, InProgressInterviewState())

        event = _event(process_id, [0])
        context = InboundContext(
            offboarding=facade,
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await InterviewTurnRecordedHandler().handle(event, context)

        facade.upsert_interview.assert_awaited_once()
        facade.start_interview.assert_awaited_once()
        facade.add_interview_turns.assert_awaited_once()
        _, kwargs = facade.upsert_interview.call_args
        expected_pid = kwargs["process_id"]
        added_pid, added_turns = facade.add_interview_turns.call_args[0]
        assert added_pid == expected_pid
        assert [t.order for t in added_turns] == [0]

    @pytest.mark.anyio
    async def test_starts_the_interview_if_still_scheduled(self) -> None:
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()
        facade.get_interview.return_value = _interview(process_id, ScheduledInterviewState())
        facade.start_interview.return_value = _interview(process_id, InProgressInterviewState())

        event = _event(process_id, [0])
        context = InboundContext(
            offboarding=facade,
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await InterviewTurnRecordedHandler().handle(event, context)

        facade.upsert_interview.assert_not_awaited()
        facade.start_interview.assert_awaited_once()
        facade.add_interview_turns.assert_awaited_once()

    @pytest.mark.anyio
    async def test_skips_turns_already_persisted_and_appends_only_new_ones(self) -> None:
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()
        facade.get_interview.return_value = _interview(
            process_id, InProgressInterviewState(), turns=[_turn(0)]
        )

        event = _event(process_id, [0, 1])
        context = InboundContext(
            offboarding=facade,
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await InterviewTurnRecordedHandler().handle(event, context)

        facade.start_interview.assert_not_awaited()
        facade.add_interview_turns.assert_awaited_once()
        _, added_turns = facade.add_interview_turns.call_args[0]
        assert [t.order for t in added_turns] == [1]

    @pytest.mark.anyio
    async def test_does_nothing_when_every_turn_is_already_persisted(self) -> None:
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()
        facade.get_interview.return_value = _interview(
            process_id, InProgressInterviewState(), turns=[_turn(0)]
        )

        event = _event(process_id, [0])
        context = InboundContext(
            offboarding=facade,
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await InterviewTurnRecordedHandler().handle(event, context)

        facade.add_interview_turns.assert_not_awaited()

    @pytest.mark.anyio
    async def test_drops_turns_for_an_already_completed_interview(self) -> None:
        """interview.completed already carries the authoritative full turn list."""
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()
        facade.get_interview.return_value = _interview(process_id, CompletedInterviewState())

        event = _event(process_id, [5])
        context = InboundContext(
            offboarding=facade,
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await InterviewTurnRecordedHandler().handle(event, context)

        facade.start_interview.assert_not_awaited()
        facade.add_interview_turns.assert_not_awaited()

    @pytest.mark.anyio
    async def test_ignores_an_empty_turns_payload(self) -> None:
        facade = AsyncMock(spec=IOffboardingServiceFacade)
        process_id = uuid4()

        event = _event(process_id, [])
        context = InboundContext(
            offboarding=facade,
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            knowledge_graph=AsyncMock(),
        )

        await InterviewTurnRecordedHandler().handle(event, context)

        facade.get_interview.assert_not_awaited()
        facade.add_interview_turns.assert_not_awaited()
