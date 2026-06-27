from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.enums import OffboardingProcessStateEnum
    from app.domain.offboarding.state import FinishedState, OffboardingProcessState


class PendingRevisionState(OffboardingProcessState):
    def get_state(self) -> OffboardingProcessStateEnum:
        return OffboardingProcessStateEnum.PENDING_REVISION
    
    def complete(self) -> OffboardingProcessState:
        return FinishedState()