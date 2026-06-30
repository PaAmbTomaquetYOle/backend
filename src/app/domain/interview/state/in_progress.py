"""IN_PROGRESS state: interview is currently underway."""

from __future__ import annotations

from app.domain.enums import InterviewStateEnum
from app.domain.interview.state.base import InterviewState
from app.domain.interview.state.cancelled import CancelledInterviewState
from app.domain.interview.state.completed import CompletedInterviewState


class InProgressInterviewState(InterviewState):
    """Represents the "In Progress" state of an interview."""

    def get_state(self) -> InterviewStateEnum:
        """Returns the IN_PROGRESS state enum value."""
        return InterviewStateEnum.IN_PROGRESS

    def complete(self) -> InterviewState:
        """Transition to COMPLETED.

        Returns:
            InterviewState: The new CompletedInterviewState instance.
        """
        return CompletedInterviewState()

    def cancel(self) -> InterviewState:
        """Transition to CANCELLED.

        Returns:
            InterviewState: The new CancelledInterviewState instance.
        """
        return CancelledInterviewState()
