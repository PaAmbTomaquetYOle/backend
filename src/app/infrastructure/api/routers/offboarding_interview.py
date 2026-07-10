"""HTTP endpoints for interview management within an offboarding process.

Writes (upsert, lifecycle transitions, adding turns) are Kafka-only — see
``domain/events/inbound_events.py`` — this router is read-only.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingInterviewFacade,
)
from app.domain import OffboardingProcessId
from app.infrastructure.api.dependencies import offboarding_interview_facade_dependency
from app.infrastructure.api.schemas.common import ErrorResponse
from app.infrastructure.api.schemas.interview import InterviewResponse, interview_to_response

router = APIRouter(tags=["interview"])

_404 = {
    404:
        {
            "model": ErrorResponse,
            "description": "Process or interview not found"
        }
}


@router.get(
    "/{process_id}/interview",
    response_model=InterviewResponse,
    responses=_404,
    summary="Get interview for an offboarding process",
)
async def get_interview(
        process_id: UUID,
        facade: Annotated[
            IOffboardingInterviewFacade,
            Depends(offboarding_interview_facade_dependency)
        ],
) -> InterviewResponse:
    """Retrieve the interview associated with an offboarding process."""
    interview = await facade.get_interview(OffboardingProcessId(process_id))
    return interview_to_response(interview)
