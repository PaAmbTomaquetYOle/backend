"""NOT_STARTED state: initial state of an offboarding process."""

from __future__ import annotations

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state.base import OffboardingProcessState
from app.domain.offboarding.state.cancelled import CancelledState
from app.domain.offboarding.state.in_progress import InProgressState


class NotStartedState(OffboardingProcessState):
    """
    Represents the "Not Started" state of the offboarding process.
    """

    def get_state(self) -> OffboardingProcessStateEnum:
        """Returns the NOT_STARTED state enum value."""
        return OffboardingProcessStateEnum.NOT_STARTED

    def start(self) -> OffboardingProcessState:
        """Transition to IN_PROGRESS.

        Returns:
            OffboardingProcessState: The new InProgressState instance.
        """
        return InProgressState()

    def cancel(self) -> OffboardingProcessState:
        """Transition to CANCELLED.

        Returns:
            OffboardingProcessState: The new CancelledState instance.
        """
        return CancelledState()
