"""FINISHED state: annual review process has been completed. Terminal state."""

from __future__ import annotations

from app.domain.annual_review.state.base import AnnualReviewProcessState
from app.domain.enums import AnnualReviewProcessStateEnum


class FinishedState(AnnualReviewProcessState):
    """Represents the 'Finished' state of the annual review process. Terminal state."""

    def get_state(self) -> AnnualReviewProcessStateEnum:
        """Returns the FINISHED state enum value."""
        return AnnualReviewProcessStateEnum.FINISHED
