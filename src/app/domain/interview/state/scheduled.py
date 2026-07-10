"""SCHEDULED state: interview has been scheduled but not yet started."""

from __future__ import annotations

from app.domain.enums import InterviewStateEnum
from app.domain.interview.state.base import InterviewState
from app.domain.interview.state.cancelled import CancelledInterviewState
from app.domain.interview.state.in_progress import InProgressInterviewState


class ScheduledInterviewState(InterviewState):
    """Represents the "Scheduled" state of an interview."""

    def get_state(self) -> InterviewStateEnum:
        """Returns the SCHEDULED state enum value."""
        return InterviewStateEnum.SCHEDULED

    def start(self) -> InterviewState:
        """Transition to IN_PROGRESS.

        Returns:
            InterviewState: The new InProgressInterviewState instance.
        """
        return InProgressInterviewState()

    def cancel(self) -> InterviewState:
        """Transition to CANCELLED.

        Returns:
            InterviewState: The new CancelledInterviewState instance.
        """
        return CancelledInterviewState()
