"""PENDING_REVISION state: annual review process is awaiting manager review."""

from __future__ import annotations

from app.domain.annual_review.state.base import AnnualReviewProcessState
from app.domain.annual_review.state.cancelled import CancelledState
from app.domain.annual_review.state.finished import FinishedState
from app.domain.enums import AnnualReviewProcessStateEnum


class PendingRevisionState(AnnualReviewProcessState):
    """Represents the 'Pending Revision' state of the annual review process."""

    def get_state(self) -> AnnualReviewProcessStateEnum:
        """Returns the PENDING_REVISION state enum value."""
        return AnnualReviewProcessStateEnum.PENDING_REVISION

    def complete(self) -> AnnualReviewProcessState:
        """Transition to FINISHED.

        Returns:
            AnnualReviewProcessState: The new FinishedState instance.
        """
        return FinishedState()

    def cancel(self) -> AnnualReviewProcessState:
        """Transition to CANCELLED.

        Returns:
            AnnualReviewProcessState: The new CancelledState instance.
        """
        return CancelledState()
