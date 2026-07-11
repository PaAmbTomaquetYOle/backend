"""Abstract base state for the AnnualReviewProcess state machine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.enums import AnnualReviewProcessStateEnum
from app.domain.exceptions import InvalidAnnualReviewProcessStateTransitionError


class AnnualReviewProcessState(ABC):
    """
    Abstract base class for annual review process states
    """
    @abstractmethod
    def get_state(self) -> AnnualReviewProcessStateEnum:
        """
        Returns the annual review process state

        Returns:
            AnnualReviewProcessStateEnum: The annual review process state
        """

    def start(self) -> AnnualReviewProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidAnnualReviewProcessStateTransitionError: Always, since the current
                state does not support starting.
        """
        raise InvalidAnnualReviewProcessStateTransitionError(
            self.get_state(), AnnualReviewProcessStateEnum.IN_PROGRESS
        )

    def submit_for_review(self) -> AnnualReviewProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidAnnualReviewProcessStateTransitionError: Always, since the current
                state does not support submitting for review.
        """
        raise InvalidAnnualReviewProcessStateTransitionError(
            self.get_state(), AnnualReviewProcessStateEnum.PENDING_REVISION
        )

    def complete(self) -> AnnualReviewProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidAnnualReviewProcessStateTransitionError: Always, since the current
                state does not support completing.
        """
        raise InvalidAnnualReviewProcessStateTransitionError(
            self.get_state(), AnnualReviewProcessStateEnum.FINISHED
        )

    def cancel(self) -> AnnualReviewProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidAnnualReviewProcessStateTransitionError: Always, since the current
                state does not support cancellation.
        """
        raise InvalidAnnualReviewProcessStateTransitionError(
            self.get_state(), AnnualReviewProcessStateEnum.CANCELLED
        )
