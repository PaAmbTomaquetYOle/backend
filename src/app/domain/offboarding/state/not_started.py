from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state import OffboardingProcessState


class NotStartedState(OffboardingProcessState):
    """
    Represents the "Not Started" state of the offboarding process.
    """

    def get_state(self) -> OffboardingProcessStateEnum:
        return OffboardingProcessStateEnum.NOT_STARTED

