"""Request/response schemas for offboarding process endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain import OffboardingProcess


class CreateOffboardingRequest(BaseModel):
    """Request body for creating a new offboarding process."""

    employee_id: UUID
    manager_id: UUID


class OffboardingProcessResponse(BaseModel):
    """Response body representing an offboarding process."""

    id: UUID
    employee_id: UUID
    manager_id: UUID
    state: str
    interview_id: UUID | None
    dossier_id: UUID | None
    created_at: datetime


def process_to_response(process: OffboardingProcess) -> OffboardingProcessResponse:
    """Convert a domain OffboardingProcess to its API response schema.

    Args:
        process: The domain aggregate to serialize.

    Returns:
        OffboardingProcessResponse: The corresponding response schema.
    """
    return OffboardingProcessResponse(
        id=process.process_id.get_id(),
        employee_id=process.employee_id.get_id(),
        manager_id=process.manager_id.get_id(),
        state=process.state_value.value,
        interview_id=process.interview_id.get_id() if process.interview_id else None,
        dossier_id=process.dossier_id.get_id() if process.dossier_id else None,
        created_at=process.created_at,
    )


class OffboardingListResponse(BaseModel):
    """Paginated list response for offboarding processes."""

    items: list[OffboardingProcessResponse]
    count: int
