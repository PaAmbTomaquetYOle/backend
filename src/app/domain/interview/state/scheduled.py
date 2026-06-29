from __future__ import annotations

from app.domain.enums import InterviewStateEnum
from app.domain.interview.state.base import InterviewState
from app.domain.interview.state.cancelled import CancelledInterviewState
from app.domain.interview.state.in_progress import InProgressInterviewState


class ScheduledInterviewState(InterviewState):
    """Represents the "Scheduled" state of an interview."""

    def get_state(self) -> InterviewStateEnum:
        return InterviewStateEnum.SCHEDULED

    def start(self) -> InterviewState:
        return InProgressInterviewState()

    def cancel(self) -> InterviewState:
        return CancelledInterviewState()
