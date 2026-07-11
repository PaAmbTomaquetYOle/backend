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

from .base_process import Process
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
    ProcessStateEnum,
    SopCandidateStatus,
    SpeakerRoleEnum,
    TaskSourceEnum,
)
from .events import (
    DomainEvent,
    DossierGenerated,
    InterviewCompleted,
    KnowledgeGraphUpdated,
    OffboardingCompleted,
    OffboardingStateChanged,
    SOPCreated,
)
from .exceptions import (
    DomainException,
    DossierAlreadyExistsForProcessError,
    DossierDomainError,
    DossierInterviewNotCompletedError,
    DossierNotFoundError,
    DossierSectionError,
    InterviewAlreadyExistsForProcessError,
    InterviewDomainError,
    InterviewNotFoundError,
    InterviewNotInProgressError,
    InterviewTurnOrderError,
    InvalidDossierStateTransitionError,
    InvalidInterviewStateTransitionError,
    InvalidOffboardingProcessStateTransitionError,
    InvalidSopCandidateTransitionError,
    InvalidStateTransitionError,
    KnowledgeGraphDomainError,
    OffboardingDomainError,
    PersonNotFoundInGraphError,
    ProcessNotFoundError,
    SopCandidateNotFoundError,
    SopDomainError,
    SopNotFoundError,
    TopicNotFoundInGraphError,
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
from .knowledge_graph import (
    ChannelNode,
    DocumentNode,
    ExpertResult,
    PersonKnowledgeProfile,
    PersonNode,
    TopicNode,
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
    OffboardingTask,
    PendingRevisionState,
    ProcessId,
)
from .sops import (
    AuthorId,
    ChannelId,
    Sop,
    SopCandidate,
    SopCandidateId,
    SopId,
)

__all__: list[str] = [
    # Base process domain
    "Process",
    # Domain events
    "DomainEvent",
    "DossierGenerated",
    "InterviewCompleted",
    "KnowledgeGraphUpdated",
    "OffboardingCompleted",
    "OffboardingStateChanged",
    "SOPCreated",
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
    "ProcessStateEnum",
    "SopCandidateStatus",
    "SpeakerRoleEnum",
    "TaskSourceEnum",
    # Exceptions
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
    # Knowledge graph domain
    "ChannelNode",
    "DocumentNode",
    "ExpertResult",
    "PersonKnowledgeProfile",
    "PersonNode",
    "TopicNode",
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
    "OffboardingTask",
    "PendingRevisionState",
    "ProcessId",
    # SOP domain
    "AuthorId",
    "ChannelId",
    "Sop",
    "SopCandidate",
    "SopCandidateId",
    "SopId",
]
