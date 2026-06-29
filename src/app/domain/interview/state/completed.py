from __future__ import annotations

from app.domain.enums import InterviewStateEnum
from app.domain.interview.state.base import InterviewState


class CompletedInterviewState(InterviewState):
    """Represents the "Completed" state of an interview. Terminal state."""

    def get_state(self) -> InterviewStateEnum:
        return InterviewStateEnum.COMPLETED
