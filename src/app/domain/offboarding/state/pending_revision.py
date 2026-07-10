"""PENDING_REVISION state: offboarding process is awaiting manager review."""

from __future__ import annotations

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state.base import OffboardingProcessState
from app.domain.offboarding.state.cancelled import CancelledState
from app.domain.offboarding.state.finished import FinishedState


class PendingRevisionState(OffboardingProcessState):
    """Represents the 'Pending Revision' state of the offboarding process."""

    def get_state(self) -> OffboardingProcessStateEnum:
        """Returns the PENDING_REVISION state enum value."""
        return OffboardingProcessStateEnum.PENDING_REVISION

    def complete(self) -> OffboardingProcessState:
        """Transition to FINISHED.

        Returns:
            OffboardingProcessState: The new FinishedState instance.
        """
        return FinishedState()

    def cancel(self) -> OffboardingProcessState:
        """Transition to CANCELLED.

        Returns:
            OffboardingProcessState: The new CancelledState instance.
        """
        return CancelledState()
