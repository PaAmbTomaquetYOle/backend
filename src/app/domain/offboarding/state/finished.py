"""FINISHED state: offboarding process has been completed. Terminal state."""

from __future__ import annotations

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state.base import OffboardingProcessState


class FinishedState(OffboardingProcessState):
    """Represents the 'Finished' state of the offboarding process. Terminal state."""

    def get_state(self) -> OffboardingProcessStateEnum:
        """Returns the FINISHED state enum value."""
        return OffboardingProcessStateEnum.FINISHED
