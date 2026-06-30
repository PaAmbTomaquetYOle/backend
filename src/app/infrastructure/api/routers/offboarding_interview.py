from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.application.service_interfaces.offboarding_facade_interface import IOffboardingInterviewFacade
from app.domain import InterviewTurn, OffboardingProcessId
from app.infrastructure.api.dependencies import offboarding_interview_facade_dependency
from app.infrastructure.api.schemas.common import ErrorResponse
from app.infrastructure.api.schemas.interview import (
    AddTurnsRequest,
    InterviewResponse,
    UpsertInterviewRequest,
    interview_to_response,
)

router = APIRouter(tags=["interview"])

_404 = {404: {"model": ErrorResponse, "description": "Process or interview not found"}}
_409 = {409: {"model": ErrorResponse, "description": "Invalid state transition"}}
_422 = {422: {"model": ErrorResponse, "description": "Validation error or invalid turn"}}


@router.put(
    "/{process_id}/interview",
    response_model=InterviewResponse,
    responses={**_404, **_422},
    summary="Upsert interview for an offboarding process (create or replace turns)",
)
async def upsert_interview(
        process_id: UUID,
        body: UpsertInterviewRequest,
        facade: Annotated[IOffboardingInterviewFacade, Depends(offboarding_interview_facade_dependency)],
        response: Response,
) -> InterviewResponse:
    pid = OffboardingProcessId(process_id)
    turns: list[InterviewTurn] = [t.to_domain() for t in body.turns]
    interview, created = await facade.upsert_interview(
        process_id=pid,
        scheduled_at=body.scheduled_at,
        turns=turns or None,
    )
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return interview_to_response(interview)


@router.get(
    "/{process_id}/interview",
    response_model=InterviewResponse,
    responses=_404,
    summary="Get interview for an offboarding process",
)
async def get_interview(
        process_id: UUID,
        facade: Annotated[IOffboardingInterviewFacade, Depends(offboarding_interview_facade_dependency)],
) -> InterviewResponse:
    interview = await facade.get_interview(OffboardingProcessId(process_id))
    return interview_to_response(interview)


@router.patch(
    "/{process_id}/interview/start",
    response_model=InterviewResponse,
    responses={**_404, **_409},
    summary="Start the interview (SCHEDULED → IN_PROGRESS)",
)
async def start_interview(
        process_id: UUID,
        facade: Annotated[IOffboardingInterviewFacade, Depends(offboarding_interview_facade_dependency)],
) -> InterviewResponse:
    interview = await facade.start_interview(OffboardingProcessId(process_id))
    return interview_to_response(interview)


@router.patch(
    "/{process_id}/interview/complete",
    response_model=InterviewResponse,
    responses={**_404, **_409},
    summary="Complete the interview (IN_PROGRESS → COMPLETED)",
)
async def complete_interview(
        process_id: UUID,
        facade: Annotated[IOffboardingInterviewFacade, Depends(offboarding_interview_facade_dependency)],
) -> InterviewResponse:
    interview = await facade.complete_interview(OffboardingProcessId(process_id))
    return interview_to_response(interview)


@router.patch(
    "/{process_id}/interview/cancel",
    response_model=InterviewResponse,
    responses={**_404, **_409},
    summary="Cancel the interview",
)
async def cancel_interview(
        process_id: UUID,
        facade: Annotated[IOffboardingInterviewFacade, Depends(offboarding_interview_facade_dependency)],
) -> InterviewResponse:
    interview = await facade.cancel_interview(OffboardingProcessId(process_id))
    return interview_to_response(interview)


@router.post(
    "/{process_id}/interview/turns",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**_404, **_422},
    summary="Add turns to an in-progress interview",
)
async def add_turns(
        process_id: UUID,
        body: AddTurnsRequest,
        facade: Annotated[IOffboardingInterviewFacade, Depends(offboarding_interview_facade_dependency)],
) -> InterviewResponse:
    pid = OffboardingProcessId(process_id)
    turns: list[InterviewTurn] = [t.to_domain() for t in body.turns]
    interview = await facade.add_interview_turns(process_id=pid, turns=turns)
    return interview_to_response(interview)
