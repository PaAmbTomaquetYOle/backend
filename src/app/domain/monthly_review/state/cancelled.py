"""CANCELLED state: monthly review process has been cancelled. Terminal state."""

from __future__ import annotations

from app.domain.enums import MonthlyReviewProcessStateEnum
from app.domain.monthly_review.state.base import MonthlyReviewProcessState


class CancelledState(MonthlyReviewProcessState):
    """Represents the "Cancelled" state of the monthly review process."""

    def get_state(self) -> MonthlyReviewProcessStateEnum:
        """Returns the CANCELLED state enum value."""
        return MonthlyReviewProcessStateEnum.CANCELLED
