"""Pydantic request/response schemas for the HTTP API layer."""

from .common import ErrorResponse
from .dossier import (
    CreateDossierRequest,
    DossierResponse,
    DossierSectionResponse,
    dossier_to_response,
)
from .interview import (
    AddTurnsRequest,
    InterviewResponse,
    UpsertInterviewRequest,
    interview_to_response,
)
from .offboarding import (
    CreateOffboardingRequest,
    OffboardingListResponse,
    OffboardingProcessResponse,
    process_to_response,
)

__all__ = [
    "AddTurnsRequest",
    "CreateDossierRequest",
    "CreateOffboardingRequest",
    "DossierResponse",
    "DossierSectionResponse",
    "ErrorResponse",
    "InterviewResponse",
    "OffboardingListResponse",
    "OffboardingProcessResponse",
    "UpsertInterviewRequest",
    "dossier_to_response",
    "interview_to_response",
    "process_to_response",
]
