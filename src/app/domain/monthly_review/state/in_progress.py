"""IN_PROGRESS state: monthly review process is actively being worked on."""

from __future__ import annotations

from app.domain.enums import MonthlyReviewProcessStateEnum
from app.domain.monthly_review.state.base import MonthlyReviewProcessState
from app.domain.monthly_review.state.cancelled import CancelledState
from app.domain.monthly_review.state.finished import FinishedState


class InProgressState(MonthlyReviewProcessState):
    """Represents the "In Progress" state of the monthly review process."""

    def get_state(self) -> MonthlyReviewProcessStateEnum:
        """Returns the IN_PROGRESS state enum value."""
        return MonthlyReviewProcessStateEnum.IN_PROGRESS

    def complete(self) -> MonthlyReviewProcessState:
        """Transition to FINISHED.

        Returns:
            MonthlyReviewProcessState: The new FinishedState instance.
        """
        return FinishedState()

    def cancel(self) -> MonthlyReviewProcessState:
        """Transition to CANCELLED.

        Returns:
            MonthlyReviewProcessState: The new CancelledState instance.
        """
        return CancelledState()
