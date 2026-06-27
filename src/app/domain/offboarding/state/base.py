from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from abc import ABC, abstractmethod

    from app.domain.enums import OffboardingProcessStateEnum
    from app.domain.exceptions import InvalidOffboardingProcessStateTransitionError


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
        """
        Starts the offboarding process

        Returns:
            OffboardingProcessState: The offboarding process state

        Raises:
            InvalidOffboardingProcessStateTransitionError: If the transition is invalid
        """
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.IN_PROGRESS
        )

    def submit_for_review(self) -> OffboardingProcessState:
        """
        Submits the offboarding process

        Returns:
            OffboardingProcessState: The offboarding process state

        Raises:
            InvalidOffboardingProcessStateTransitionError: If the transition is invalid
        """
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.PENDING_REVISION
        )

    def complete(self) -> OffboardingProcessState:
        """
        Completes the offboarding process

        Returns:
            OffboardingProcessState: The offboarding process state

        Raises:
            InvalidOffboardingProcessStateTransitionError: If the transition is invalid
        """
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.FINISHED
        )
