from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state import OffboardingProcessState, PendingRevisionState


class InProgressState(OffboardingProcessState):
    """
    Represents the "In Progress" state.
    """

    def get_state(self) -> OffboardingProcessStateEnum:
        return OffboardingProcessStateEnum.IN_PROGRESS
    
    def submit_for_review(self) -> OffboardingProcessState:
        return PendingRevisionState()
