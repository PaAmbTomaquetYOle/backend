"""Domain exceptions package.

This package contains the base exception type and any domain-specific
exceptions raised by the domain layer.
"""

from .auth import AuthDomainError, InvalidCredentialsError
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
from .knowledge_graph import (
    KnowledgeGraphDomainError,
    PersonNotFoundInGraphError,
    TopicNotFoundInGraphError,
)
from .offboarding import (
    OffboardingDomainError,
    ProcessNotFoundError,
)
from .sops import (
    InvalidSopCandidateTransitionError,
    SopCandidateNotFoundError,
    SopDomainError,
    SopNotFoundError,
)

__all__ = [
    "AuthDomainError",
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
    "InvalidCredentialsError",
    "InvalidDossierStateTransitionError",
    "InvalidInterviewStateTransitionError",
    "InvalidOffboardingProcessStateTransitionError",
    "InvalidSopCandidateTransitionError",
    "InvalidStateTransitionError",
    "KnowledgeGraphDomainError",
    "OffboardingDomainError",
    "PersonNotFoundInGraphError",
    "ProcessNotFoundError",
    "SopCandidateNotFoundError",
    "SopDomainError",
    "SopNotFoundError",
    "TopicNotFoundInGraphError",
]
