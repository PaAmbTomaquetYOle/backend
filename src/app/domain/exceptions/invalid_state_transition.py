"""Exceptions raised when an invalid state machine transition is attempted."""

from app.domain.enums import (
    AnnualReviewProcessStateEnum,
    DossierStateEnum,
    InterviewStateEnum,
    MonthlyReviewProcessStateEnum,
    OffboardingProcessStateEnum,
)
from app.domain.exceptions.base import DomainException


class InvalidStateTransitionError(DomainException):
    """
    Exception raised when an invalid state transition is attempted.
    """

    def __init__(self, current_state: str, attempted_transition: str):
        """Initialize with the invalid transition details.

        Args:
            current_state: The state the entity was in when the transition was attempted.
            attempted_transition: The state the entity was trying to transition to.
        """
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
        """Initialize with the offboarding process states involved in the invalid transition.

        Args:
            current_state: The offboarding process state at the time of the attempt.
            attempted_transition: The offboarding process state that was not reachable.
        """
        self.current_state = current_state
        self.attempted_transition = attempted_transition
        super().__init__(
            current_state=current_state.name,
            attempted_transition=attempted_transition.name
        )


class InvalidMonthlyReviewProcessStateTransitionError(InvalidStateTransitionError):
    """
    Exception raised when an invalid state transition is attempted in a monthly review process.
    """

    def __init__(
            self,
            current_state: MonthlyReviewProcessStateEnum,
            attempted_transition: MonthlyReviewProcessStateEnum
    ):
        """Initialize with the monthly review process states involved in the invalid transition.

        Args:
            current_state: The monthly review process state at the time of the attempt.
            attempted_transition: The monthly review process state that was not reachable.
        """
        self.current_state = current_state
        self.attempted_transition = attempted_transition
        super().__init__(
            current_state=current_state.name,
            attempted_transition=attempted_transition.name
        )


class InvalidAnnualReviewProcessStateTransitionError(InvalidStateTransitionError):
    """
    Exception raised when an invalid state transition is attempted in an annual review process.
    """

    def __init__(
            self,
            current_state: AnnualReviewProcessStateEnum,
            attempted_transition: AnnualReviewProcessStateEnum
    ):
        """Initialize with the annual review process states involved in the invalid transition.

        Args:
            current_state: The annual review process state at the time of the attempt.
            attempted_transition: The annual review process state that was not reachable.
        """
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
        """Initialize with the interview states involved in the invalid transition.

        Args:
            current_state: The interview state at the time of the attempt.
            attempted_transition: The interview state that was not reachable.
        """
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
        """Initialize with the dossier states involved in the invalid transition.

        Args:
            current_state: The dossier state at the time of the attempt.
            attempted_transition: The dossier state that was not reachable.
        """
        self.current_state = current_state
        self.attempted_transition = attempted_transition
        super().__init__(
            current_state=current_state.name,
            attempted_transition=attempted_transition.name
        )