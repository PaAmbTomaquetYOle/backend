"""NOT_STARTED state: initial state of a monthly review process."""

from __future__ import annotations

from app.domain.enums import MonthlyReviewProcessStateEnum
from app.domain.monthly_review.state.base import MonthlyReviewProcessState
from app.domain.monthly_review.state.cancelled import CancelledState
from app.domain.monthly_review.state.in_progress import InProgressState


class NotStartedState(MonthlyReviewProcessState):
    """
    Represents the "Not Started" state of the monthly review process.
    """

    def get_state(self) -> MonthlyReviewProcessStateEnum:
        """Returns the NOT_STARTED state enum value."""
        return MonthlyReviewProcessStateEnum.NOT_STARTED

    def start(self) -> MonthlyReviewProcessState:
        """Transition to IN_PROGRESS.

        Returns:
            MonthlyReviewProcessState: The new InProgressState instance.
        """
        return InProgressState()

    def cancel(self) -> MonthlyReviewProcessState:
        """Transition to CANCELLED.

        Returns:
            MonthlyReviewProcessState: The new CancelledState instance.
        """
        return CancelledState()
