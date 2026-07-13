"""NOT_STARTED state: initial state of an annual review process."""

from __future__ import annotations

from app.domain.annual_review.state.base import AnnualReviewProcessState
from app.domain.annual_review.state.cancelled import CancelledState
from app.domain.annual_review.state.in_progress import InProgressState
from app.domain.enums import AnnualReviewProcessStateEnum


class NotStartedState(AnnualReviewProcessState):
    """
    Represents the "Not Started" state of the annual review process.
    """

    def get_state(self) -> AnnualReviewProcessStateEnum:
        """Returns the NOT_STARTED state enum value."""
        return AnnualReviewProcessStateEnum.NOT_STARTED

    def start(self) -> AnnualReviewProcessState:
        """Transition to IN_PROGRESS.

        Returns:
            AnnualReviewProcessState: The new InProgressState instance.
        """
        return InProgressState()

    def cancel(self) -> AnnualReviewProcessState:
        """Transition to CANCELLED.

        Returns:
            AnnualReviewProcessState: The new CancelledState instance.
        """
        return CancelledState()
