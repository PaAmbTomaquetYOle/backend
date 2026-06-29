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
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.IN_PROGRESS
        )

    def submit_for_review(self) -> OffboardingProcessState:
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.PENDING_REVISION
        )

    def complete(self) -> OffboardingProcessState:
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.FINISHED
        )

    def cancel(self) -> OffboardingProcessState:
        raise InvalidOffboardingProcessStateTransitionError(
            self.get_state(), OffboardingProcessStateEnum.CANCELLED
        )
