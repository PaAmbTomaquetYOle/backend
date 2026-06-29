"""Domain layer: pure business logic, entities, value objects and ports.

This is the innermost layer and the heart of the system. It models the business
in plain Python and depends on *nothing* outside the standard library — no
FastAPI, no pydantic-settings, no external SDKs, no I/O. Both ``application`` and
``infrastructure`` may depend on it; it depends on neither of them.

What goes here:
- Entities and aggregates (objects with identity and invariants).
- Value objects (immutable, equality by value).
- Domain ports: interfaces expressed in pure domain language (e.g. a repository
  for an aggregate), defining what the domain needs without naming a technology.
- Domain services and domain events that encode business rules.

What does NOT go here:
- Frameworks or I/O of any kind, configuration, HTTP/persistence concerns, or
  use-case orchestration (that is ``application``).

Distinguish domain ports from ``application.ports``: domain ports speak the
business vocabulary, while application ports describe what the use cases need
from external systems.

Empty for now. As domain types are added, export them here and list them in
``__all__``.
"""

from .dossier import (
    ApprovedDossierState,
    CancelledDossierState,
    Contact,
    ContactsSection,
    Dossier,
    DossierSection,
    DossierState,
    DraftDossierState,
    GeneratingDossierState,
    KnowledgeArea,
    KnowledgeAreasSection,
    NotGeneratedDossierState,
    PendingTask,
    PendingTasksSection,
    ResponsibilitiesSection,
    UnderReviewDossierState,
)
from .enums import (
    DossierStateEnum,
    InterviewStateEnum,
    OffboardingProcessStateEnum,
    SpeakerRoleEnum,
)
from .exceptions import (
    DomainException,
    DossierAlreadyExistsForProcessError,
    DossierDomainError,
    DossierInterviewNotCompletedError,
    DossierSectionError,
    InterviewAlreadyExistsForProcessError,
    InterviewDomainError,
    InterviewNotInProgressError,
    InterviewTurnOrderError,
    InvalidDossierStateTransitionError,
    InvalidInterviewStateTransitionError,
    InvalidOffboardingProcessStateTransitionError,
    InvalidStateTransitionError,
)
from .interview import (
    CancelledInterviewState,
    CompletedInterviewState,
    InProgressInterviewState,
    Interview,
    InterviewNote,
    InterviewQuestion,
    InterviewState,
    InterviewTurn,
    ScheduledInterviewState,
)
from .offboarding import (
    CancelledState,
    DossierId,
    EmployeeId,
    FinishedState,
    Id,
    InProgressState,
    InterviewId,
    ManagerId,
    NotStartedState,
    OffboardingProcess,
    OffboardingProcessId,
    OffboardingProcessState,
    PendingRevisionState,
    ProcessId,
)

__all__: list[str] = [
    # Dossier domain
    "ApprovedDossierState",
    "CancelledDossierState",
    "Contact",
    "ContactsSection",
    "Dossier",
    "DossierSection",
    "DossierState",
    "DraftDossierState",
    "GeneratingDossierState",
    "KnowledgeArea",
    "KnowledgeAreasSection",
    "NotGeneratedDossierState",
    "PendingTask",
    "PendingTasksSection",
    "ResponsibilitiesSection",
    "UnderReviewDossierState",
    # Enums
    "DossierStateEnum",
    "InterviewStateEnum",
    "OffboardingProcessStateEnum",
    "SpeakerRoleEnum",
    # Exceptions
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
    # Interview domain
    "CancelledInterviewState",
    "CompletedInterviewState",
    "InProgressInterviewState",
    "Interview",
    "InterviewNote",
    "InterviewQuestion",
    "InterviewState",
    "InterviewTurn",
    "ScheduledInterviewState",
    # Offboarding domain
    "CancelledState",
    "DossierId",
    "EmployeeId",
    "FinishedState",
    "Id",
    "InProgressState",
    "InterviewId",
    "ManagerId",
    "NotStartedState",
    "OffboardingProcess",
    "OffboardingProcessId",
    "OffboardingProcessState",
    "PendingRevisionState",
    "ProcessId",
]
