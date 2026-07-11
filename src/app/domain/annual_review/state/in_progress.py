"""IN_PROGRESS state: annual review process is actively being worked on."""

from __future__ import annotations

from app.domain.annual_review.state.base import AnnualReviewProcessState
from app.domain.annual_review.state.cancelled import CancelledState
from app.domain.annual_review.state.pending_revision import PendingRevisionState
from app.domain.enums import AnnualReviewProcessStateEnum


class InProgressState(AnnualReviewProcessState):
    """Represents the "In Progress" state of the annual review process."""

    def get_state(self) -> AnnualReviewProcessStateEnum:
        """Returns the IN_PROGRESS state enum value."""
        return AnnualReviewProcessStateEnum.IN_PROGRESS

    def submit_for_review(self) -> AnnualReviewProcessState:
        """Transition to PENDING_REVISION.

        Returns:
            AnnualReviewProcessState: The new PendingRevisionState instance.
        """
        return PendingRevisionState()

    def cancel(self) -> AnnualReviewProcessState:
        """Transition to CANCELLED.

        Returns:
            AnnualReviewProcessState: The new CancelledState instance.
        """
        return CancelledState()
