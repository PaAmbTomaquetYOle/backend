from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.enums import OffboardingProcessStateEnum
    from app.domain.offboarding.state import InProgressState, OffboardingProcessState


class NotStartedState(OffboardingProcessState):
    """
    Represents the "Not Started" state of the offboarding process.
    """

    def get_state(self) -> OffboardingProcessStateEnum:
        return OffboardingProcessStateEnum.NOT_STARTED

    def start(self) -> OffboardingProcessState:
        return InProgressState()