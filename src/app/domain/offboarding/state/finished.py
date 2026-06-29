from __future__ import annotations

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state.base import OffboardingProcessState


class FinishedState(OffboardingProcessState):
    def get_state(self) -> OffboardingProcessStateEnum:
        return OffboardingProcessStateEnum.FINISHED