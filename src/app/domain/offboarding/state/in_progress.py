from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state import OffboardingProcessState


class InProgressState(OffboardingProcessState):
    """
    Represents the "In Progress" state.
    """

    def get_state(self) -> OffboardingProcessStateEnum:
        return OffboardingProcessStateEnum.IN_PROGRESS