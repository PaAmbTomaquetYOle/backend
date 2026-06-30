"""IN_PROGRESS state: offboarding process is actively being worked on."""

from __future__ import annotations

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state.base import OffboardingProcessState
from app.domain.offboarding.state.cancelled import CancelledState
from app.domain.offboarding.state.pending_revision import PendingRevisionState


class InProgressState(OffboardingProcessState):
    """Represents the "In Progress" state of the offboarding process."""

    def get_state(self) -> OffboardingProcessStateEnum:
        """Returns the IN_PROGRESS state enum value."""
        return OffboardingProcessStateEnum.IN_PROGRESS

    def submit_for_review(self) -> OffboardingProcessState:
        """Transition to PENDING_REVISION.

        Returns:
            OffboardingProcessState: The new PendingRevisionState instance.
        """
        return PendingRevisionState()

    def cancel(self) -> OffboardingProcessState:
        """Transition to CANCELLED.

        Returns:
            OffboardingProcessState: The new CancelledState instance.
        """
        return CancelledState()
