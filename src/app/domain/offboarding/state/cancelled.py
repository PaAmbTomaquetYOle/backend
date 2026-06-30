"""CANCELLED state: offboarding process has been cancelled. Terminal state."""

from __future__ import annotations

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state.base import OffboardingProcessState


class CancelledState(OffboardingProcessState):
    """Represents the "Cancelled" state of the offboarding process."""

    def get_state(self) -> OffboardingProcessStateEnum:
        """Returns the CANCELLED state enum value."""
        return OffboardingProcessStateEnum.CANCELLED
