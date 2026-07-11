"""FINISHED state: monthly review process has been completed. Terminal state."""

from __future__ import annotations

from app.domain.enums import MonthlyReviewProcessStateEnum
from app.domain.monthly_review.state.base import MonthlyReviewProcessState


class FinishedState(MonthlyReviewProcessState):
    """Represents the 'Finished' state of the monthly review process. Terminal state."""

    def get_state(self) -> MonthlyReviewProcessStateEnum:
        """Returns the FINISHED state enum value."""
        return MonthlyReviewProcessStateEnum.FINISHED
