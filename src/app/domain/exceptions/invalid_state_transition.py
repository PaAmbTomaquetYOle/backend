from app.domain.enums import DossierStateEnum, InterviewStateEnum, OffboardingProcessStateEnum
from app.domain.exceptions.base import DomainException


class InvalidStateTransitionError(DomainException):
    """
    Exception raised when an invalid state transition is attempted.
    """

    def __init__(self, current_state: str, attempted_transition: str):
        self.current_state = current_state
        self.attempted_transition = attempted_transition
        super().__init__(f"Invalid state transition from {current_state} to {attempted_transition}")


class InvalidOffboardingProcessStateTransitionError(InvalidStateTransitionError):
    """
    Exception raised when an invalid state transition is attempted in the offboarding process.
    """

    def __init__(
            self,
            current_state: OffboardingProcessStateEnum,
            attempted_transition: OffboardingProcessStateEnum
    ):
        self.current_state = current_state
        self.attempted_transition = attempted_transition
        super().__init__(
            current_state=current_state.name,
            attempted_transition=attempted_transition.name
        )


class InvalidInterviewStateTransitionError(InvalidStateTransitionError):
    """
    Exception raised when an invalid state transition is attempted in an interview.
    """

    def __init__(self, current_state: InterviewStateEnum, attempted_transition: InterviewStateEnum):
        self.current_state = current_state
        self.attempted_transition = attempted_transition
        super().__init__(
            current_state=current_state.name,
            attempted_transition=attempted_transition.name
        )


class InvalidDossierStateTransitionError(InvalidStateTransitionError):
    """
    Exception raised when an invalid state transition is attempted in a dossier.
    """

    def __init__(self, current_state: DossierStateEnum, attempted_transition: DossierStateEnum):
        self.current_state = current_state
        self.attempted_transition = attempted_transition
        super().__init__(
            current_state=current_state.name,
            attempted_transition=attempted_transition.name
        )