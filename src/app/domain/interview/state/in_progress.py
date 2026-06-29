from __future__ import annotations

from app.domain.enums import InterviewStateEnum
from app.domain.interview.state.base import InterviewState
from app.domain.interview.state.cancelled import CancelledInterviewState
from app.domain.interview.state.completed import CompletedInterviewState


class InProgressInterviewState(InterviewState):
    """Represents the "In Progress" state of an interview."""

    def get_state(self) -> InterviewStateEnum:
        return InterviewStateEnum.IN_PROGRESS

    def complete(self) -> InterviewState:
        return CompletedInterviewState()

    def cancel(self) -> InterviewState:
        return CancelledInterviewState()
