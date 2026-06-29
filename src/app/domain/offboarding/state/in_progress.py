from __future__ import annotations

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state.base import OffboardingProcessState
from app.domain.offboarding.state.cancelled import CancelledState
from app.domain.offboarding.state.pending_revision import PendingRevisionState


class InProgressState(OffboardingProcessState):
    """
    Represents the "In Progress" state.
    """

    def get_state(self) -> OffboardingProcessStateEnum:
        return OffboardingProcessStateEnum.IN_PROGRESS

    def submit_for_review(self) -> OffboardingProcessState:
        return PendingRevisionState()

    def cancel(self) -> OffboardingProcessState:
        return CancelledState()
