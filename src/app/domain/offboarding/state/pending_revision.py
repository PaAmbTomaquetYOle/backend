from __future__ import annotations

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state.base import OffboardingProcessState
from app.domain.offboarding.state.cancelled import CancelledState
from app.domain.offboarding.state.finished import FinishedState


class PendingRevisionState(OffboardingProcessState):
    def get_state(self) -> OffboardingProcessStateEnum:
        return OffboardingProcessStateEnum.PENDING_REVISION

    def complete(self) -> OffboardingProcessState:
        return FinishedState()

    def cancel(self) -> OffboardingProcessState:
        return CancelledState()
