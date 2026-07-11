"""CANCELLED state: annual review process has been cancelled. Terminal state."""

from __future__ import annotations

from app.domain.annual_review.state.base import AnnualReviewProcessState
from app.domain.enums import AnnualReviewProcessStateEnum


class CancelledState(AnnualReviewProcessState):
    """Represents the "Cancelled" state of the annual review process."""

    def get_state(self) -> AnnualReviewProcessStateEnum:
        """Returns the CANCELLED state enum value."""
        return AnnualReviewProcessStateEnum.CANCELLED
