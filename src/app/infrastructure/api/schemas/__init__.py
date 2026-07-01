"""Pydantic request/response schemas for the HTTP API layer."""

from .common import ErrorResponse
from .dossier import (
    CreateDossierRequest,
    DossierResponse,
    DossierSearchListResponse,
    DossierSearchResultResponse,
    DossierSectionResponse,
    dossier_search_result_to_response,
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
    "DossierSearchListResponse",
    "DossierSearchResultResponse",
    "DossierSectionResponse",
    "ErrorResponse",
    "InterviewResponse",
    "OffboardingListResponse",
    "OffboardingProcessResponse",
    "UpsertInterviewRequest",
    "dossier_search_result_to_response",
    "dossier_to_response",
    "interview_to_response",
    "process_to_response",
]
