"""HTTP endpoints for offboarding process management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingProcessFacade,
)
from app.domain import EmployeeId, ManagerId, OffboardingProcessId
from app.domain.enums import OffboardingProcessStateEnum
from app.infrastructure.api.dependencies import offboarding_process_facade_dependency
from app.infrastructure.api.routers.offboarding_dossier import router as dossier_router
from app.infrastructure.api.routers.offboarding_interview import router as interview_router
from app.infrastructure.api.schemas.common import ErrorResponse
from app.infrastructure.api.schemas.offboarding import (
    CreateOffboardingRequest,
    OffboardingListResponse,
    OffboardingProcessResponse,
    process_to_response,
)

router = APIRouter(
    prefix="/offboarding",
    tags=["offboarding"],
    dependencies=[Depends(get_current_service)],
)
router.include_router(interview_router)
router.include_router(dossier_router)

_404 = {
    404:
        {
            "model": ErrorResponse,
            "description": "Process not found"
        }
}
_409 = {
    409:
        {
            "model": ErrorResponse,
              "description": "Invalid state transition or constraint violation"
        }
}


@router.post(
    "",
    response_model=OffboardingProcessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new offboarding process",
)
async def create_offboarding(
        body: CreateOffboardingRequest,
        facade: Annotated[
            IOffboardingProcessFacade,
            Depends(offboarding_process_facade_dependency)
        ],
) -> OffboardingProcessResponse:
    """Create a new offboarding process for an employee."""
    process = await facade.create_offboarding(
        employee_id=EmployeeId(body.employee_id),
        manager_id=ManagerId(body.manager_id),
        employee_name=body.employee_name,
        manager_name=body.manager_name,
    )
    return process_to_response(process)


@router.get(
    "",
    response_model=OffboardingListResponse,
    summary="List offboarding processes with optional filters",
)
async def list_offboardings(
        facade: Annotated[
            IOffboardingProcessFacade,
            Depends(offboarding_process_facade_dependency)
        ],
        employee_id: Annotated[str | None, Query(description="Filter by employee ID (Slack user ID)")] = None,
        manager_id: Annotated[str | None, Query(description="Filter by manager ID (Slack user ID)")] = None,
        state: Annotated[
            str | None,
            Query(description="Filter by state value (e.g. not_started)")
        ] = None,
) -> OffboardingListResponse:
    """List offboarding processes, optionally filtered by employee, manager, or state."""
    state_enum: OffboardingProcessStateEnum | None = None
    if state is not None:
        try:
            state_enum = OffboardingProcessStateEnum(state)
        except ValueError:
            valid = [e.value for e in OffboardingProcessStateEnum]
            raise HTTPException(
                status_code=422,
                detail=f"Invalid state '{state}'. Valid values: {valid}"
            )
    processes = await facade.list_offboardings(
        employee_id=EmployeeId(employee_id) if employee_id else None,
        manager_id=ManagerId(manager_id) if manager_id else None,
        state=state_enum,
    )
    items = [process_to_response(p) for p in processes]
    return OffboardingListResponse(items=items, count=len(items))


@router.get(
    "/{process_id}",
    response_model=OffboardingProcessResponse,
    responses=_404,
    summary="Get an offboarding process by ID",
)
async def get_offboarding(
        process_id: UUID,
        facade: Annotated[
            IOffboardingProcessFacade,
            Depends(offboarding_process_facade_dependency)
        ],
) -> OffboardingProcessResponse:
    """Retrieve a specific offboarding process by its ID."""
    process = await facade.get_offboarding(OffboardingProcessId(process_id))
    return process_to_response(process)


@router.delete(
    "/{process_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_404,
    summary="Delete an offboarding process",
)
async def delete_offboarding(
        process_id: UUID,
        facade: Annotated[
            IOffboardingProcessFacade,
            Depends(offboarding_process_facade_dependency)
        ],
) -> None:
    """Delete an offboarding process by its ID."""
    await facade.delete_offboarding(OffboardingProcessId(process_id))


@router.patch(
    "/{process_id}/start",
    response_model=OffboardingProcessResponse,
    responses={**_404, **_409},
    summary="Start the offboarding process (NOT_STARTED → IN_PROGRESS)",
)
async def start_offboarding(
        process_id: UUID,
        facade: Annotated[
            IOffboardingProcessFacade,
            Depends(offboarding_process_facade_dependency)
        ],
) -> OffboardingProcessResponse:
    """Transition an offboarding process from NOT_STARTED to IN_PROGRESS."""
    process = await facade.start_offboarding(OffboardingProcessId(process_id))
    return process_to_response(process)


@router.patch(
    "/{process_id}/submit-for-review",
    response_model=OffboardingProcessResponse,
    responses={**_404, **_409},
    summary="Submit the offboarding process for review (IN_PROGRESS → PENDING_REVISION)",
)
async def submit_for_review(
        process_id: UUID,
        facade: Annotated[
            IOffboardingProcessFacade,
            Depends(offboarding_process_facade_dependency)
        ],
) -> OffboardingProcessResponse:
    """Transition an offboarding process from IN_PROGRESS to PENDING_REVISION."""
    process = await facade.submit_offboarding_for_review(OffboardingProcessId(process_id))
    return process_to_response(process)


@router.patch(
    "/{process_id}/complete",
    response_model=OffboardingProcessResponse,
    responses={**_404, **_409},
    summary="Complete the offboarding process (PENDING_REVISION → FINISHED)",
)
async def complete_offboarding(
        process_id: UUID,
        facade: Annotated[
            IOffboardingProcessFacade,
            Depends(offboarding_process_facade_dependency)
        ],
) -> OffboardingProcessResponse:
    """Transition an offboarding process from PENDING_REVISION to FINISHED."""
    process = await facade.complete_offboarding(OffboardingProcessId(process_id))
    return process_to_response(process)


@router.patch(
    "/{process_id}/cancel",
    response_model=OffboardingProcessResponse,
    responses={**_404, **_409},
    summary="Cancel the offboarding process",
)
async def cancel_offboarding(
        process_id: UUID,
        facade: Annotated[
            IOffboardingProcessFacade,
            Depends(offboarding_process_facade_dependency)
        ],
) -> OffboardingProcessResponse:
    """Cancel an offboarding process."""
    process = await facade.cancel_offboarding(OffboardingProcessId(process_id))
    return process_to_response(process)
