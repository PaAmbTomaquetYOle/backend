"""Unit tests for the Interview aggregate root."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.domain.enums import InterviewStateEnum, SpeakerRoleEnum
from app.domain.exceptions.interview import InterviewNotInProgressError
from app.domain.interview.interview import Interview
from app.domain.interview.state.in_progress import InProgressInterviewState
from app.domain.interview.state.scheduled import ScheduledInterviewState
from app.domain.interview.turn import InterviewNote, InterviewQuestion
from app.domain.offboarding.id import InterviewId, OffboardingProcessId

DT = datetime(2024, 1, 1, 12, 0, 0)


def make_interview(state=None) -> Interview:
    return Interview(
        interview_id=InterviewId(),
        process_id=OffboardingProcessId(),
        state=state or ScheduledInterviewState(),
        scheduled_at=DT,
        created_at=DT,
    )


def make_question() -> InterviewQuestion:
    return InterviewQuestion(
        speaker_role=SpeakerRoleEnum.INTERVIEWER,
        timestamp=DT,
        content="What are your main responsibilities?",
        order=1,
    )


def make_note() -> InterviewNote:
    return InterviewNote(
        speaker_role=SpeakerRoleEnum.INTERVIEWER,
        timestamp=DT,
        content="Candidate seemed confident.",
        order=2,
    )


class TestInterviewConstruction:
    def test_properties_are_accessible(self):
        interview_id = InterviewId()
        process_id = OffboardingProcessId()
        interview = Interview(
            interview_id=interview_id,
            process_id=process_id,
            state=ScheduledInterviewState(),
            scheduled_at=DT,
            created_at=DT,
        )
        assert interview.interview_id is interview_id
        assert interview.process_id is process_id
        assert interview.scheduled_at == DT
        assert interview.created_at == DT
        assert interview.state.get_state() == InterviewStateEnum.SCHEDULED


class TestInterviewStateTransitions:
    def test_start_transitions_to_in_progress(self):
        interview = make_interview()
        interview.start()
        assert interview.state.get_state() == InterviewStateEnum.IN_PROGRESS

    def test_complete_from_in_progress(self):
        interview = make_interview(state=InProgressInterviewState())
        interview.complete()
        assert interview.state.get_state() == InterviewStateEnum.COMPLETED

    def test_cancel_from_scheduled(self):
        interview = make_interview()
        interview.cancel()
        assert interview.state.get_state() == InterviewStateEnum.CANCELLED


class TestInterviewTurns:
    def test_add_turn_when_in_progress(self):
        interview = make_interview(state=InProgressInterviewState())
        question = make_question()
        interview.add_turn(question)
        assert question in interview.turns

    def test_add_turn_when_not_in_progress_raises(self):
        interview = make_interview()
        with pytest.raises(InterviewNotInProgressError):
            interview.add_turn(make_question())

    def test_turns_returns_defensive_copy(self):
        interview = make_interview(state=InProgressInterviewState())
        interview.add_turn(make_question())
        turns_copy = interview.turns
        turns_copy.clear()
        assert len(interview.turns) == 1


class TestInterviewTurnTypes:
    def test_interview_question_get_turn_type(self):
        question = make_question()
        assert question.get_turn_type() == "question"

    def test_interview_note_get_turn_type(self):
        note = make_note()
        assert note.get_turn_type() == "note"

    def test_interview_question_answer_text_setter(self):
        question = make_question()
        assert question.answer_text is None
        question.answer_text = "I handle deployments."
        assert question.answer_text == "I handle deployments."
