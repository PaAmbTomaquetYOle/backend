"""Abstract base state for the OffboardingProcess state machine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.exceptions import InvalidOffboardingProcessStateTransitionError

if TYPE_CHECKING:
    pass


class OffboardingProcessState(ABC):
    """
    Abstract base class for offboarding process states
    """
    @abstractmethod
    def get_state(self) -> OffboardingProcessStateEnum:
        """
        Returns the offboarding process state

        Returns:
            OffboardingProcessStateEnum: The offboarding process state
        """

    def start(self) -> OffboardingProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidOffboardingProcessStateTransitionError: Always, since the current
                state does not support starting.
        """
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.IN_PROGRESS
        )

    def submit_for_review(self) -> OffboardingProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidOffboardingProcessStateTransitionError: Always, since the current
                state does not support submitting for review.
        """
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.PENDING_REVISION
        )

    def complete(self) -> OffboardingProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidOffboardingProcessStateTransitionError: Always, since the current
                state does not support completing.
        """
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.FINISHED
        )

    def cancel(self) -> OffboardingProcessState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidOffboardingProcessStateTransitionError: Always, since the current
                state does not support cancellation.
        """
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.CANCELLED
        )
