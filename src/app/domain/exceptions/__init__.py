"""Domain exceptions package.

This package contains the base exception type and any domain-specific
exceptions raised by the domain layer.
"""

from .base import DomainException
from .dossier import (
    DossierAlreadyExistsForProcessError,
    DossierDomainError,
    DossierInterviewNotCompletedError,
    DossierNotFoundError,
    DossierSectionError,
)
from .interview import (
    InterviewAlreadyExistsForProcessError,
    InterviewDomainError,
    InterviewNotFoundError,
    InterviewNotInProgressError,
    InterviewTurnOrderError,
)
from .invalid_state_transition import (
    InvalidDossierStateTransitionError,
    InvalidInterviewStateTransitionError,
    InvalidOffboardingProcessStateTransitionError,
    InvalidStateTransitionError,
)
from .offboarding import (
    OffboardingDomainError,
    ProcessNotFoundError,
)
from .sops import (
    SopDomainError,
    SopNotFoundError,
)

__all__ = [
    "DomainException",
    "DossierAlreadyExistsForProcessError",
    "DossierDomainError",
    "DossierInterviewNotCompletedError",
    "DossierNotFoundError",
    "DossierSectionError",
    "InterviewAlreadyExistsForProcessError",
    "InterviewDomainError",
    "InterviewNotFoundError",
    "InterviewNotInProgressError",
    "InterviewTurnOrderError",
    "InvalidDossierStateTransitionError",
    "InvalidInterviewStateTransitionError",
    "InvalidOffboardingProcessStateTransitionError",
    "InvalidStateTransitionError",
    "OffboardingDomainError",
    "ProcessNotFoundError",
    "SopDomainError",
    "SopNotFoundError",
]
