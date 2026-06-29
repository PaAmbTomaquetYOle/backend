"""Domain exceptions package.

This package contains the base exception type and any domain-specific
exceptions raised by the domain layer.
"""

from .base import DomainException
from .dossier import (
    DossierAlreadyExistsForProcessError,
    DossierDomainError,
    DossierSectionError,
    DossierInterviewNotCompletedError,
)
from .interview import (
    InterviewAlreadyExistsForProcessError,
    InterviewDomainError,
    InterviewNotInProgressError,
    InterviewTurnOrderError,
)
from .invalid_state_transition import (
    InvalidDossierStateTransitionError,
    InvalidInterviewStateTransitionError,
    InvalidOffboardingProcessStateTransitionError,
    InvalidStateTransitionError,
)

__all__ = [
    "DomainException",
    "DossierAlreadyExistsForProcessError",
    "DossierDomainError",
    "DossierSectionError",
    "InterviewAlreadyExistsForProcessError",
    "InterviewDomainError",
    "DossierInterviewNotCompletedError",
    "InterviewNotInProgressError",
    "InterviewTurnOrderError",
    "InvalidDossierStateTransitionError",
    "InvalidInterviewStateTransitionError",
    "InvalidOffboardingProcessStateTransitionError",
    "InvalidStateTransitionError",
]
