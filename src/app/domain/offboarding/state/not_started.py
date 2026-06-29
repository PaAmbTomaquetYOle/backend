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
        return OffboardingProcessStateEnum.NOT_STARTED

    def start(self) -> OffboardingProcessState:
        return InProgressState()

    def cancel(self) -> OffboardingProcessState:
        return CancelledState()
