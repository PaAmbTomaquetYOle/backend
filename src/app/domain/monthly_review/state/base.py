"""Abstract base state for the MonthlyReviewProcess state machine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.enums import MonthlyReviewProcessStateEnum
from app.domain.exceptions import InvalidMonthlyReviewProcessStateTransitionError


class MonthlyReviewProcessState(ABC):
    """
    Abstract base class for monthly review process states
    """
    @abstractmethod
    def get_state(self) -> MonthlyReviewProcessStateEnum:
        """
        Returns the monthly review process state

        Returns:
            MonthlyReviewProcessStateEnum: The monthly review process state
        """

    def start(self) -> MonthlyReviewProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidMonthlyReviewProcessStateTransitionError: Always, since the current
                state does not support starting.
        """
        raise InvalidMonthlyReviewProcessStateTransitionError(
            self.get_state(), MonthlyReviewProcessStateEnum.IN_PROGRESS
        )

    def complete(self) -> MonthlyReviewProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidMonthlyReviewProcessStateTransitionError: Always, since the current
                state does not support completing.
        """
        raise InvalidMonthlyReviewProcessStateTransitionError(
            self.get_state(), MonthlyReviewProcessStateEnum.FINISHED
        )

    def cancel(self) -> MonthlyReviewProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidMonthlyReviewProcessStateTransitionError: Always, since the current
                state does not support cancellation.
        """
        raise InvalidMonthlyReviewProcessStateTransitionError(
            self.get_state(), MonthlyReviewProcessStateEnum.CANCELLED
        )
