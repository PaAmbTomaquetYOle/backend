"""HTTP endpoints for offboarding process management.

Writes (create, delete, lifecycle transitions) are Kafka-only — see
``domain/events/inbound_events.py`` — this router is read-only.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingProcessFacade,
)
from app.domain import EmployeeId, ManagerId, OffboardingProcessId
from app.domain.enums import OffboardingProcessStateEnum
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.api.dependencies import offboarding_process_facade_dependency
from app.infrastructure.api.routers.offboarding_dossier import router as dossier_router
from app.infrastructure.api.routers.offboarding_interview import router as interview_router
from app.infrastructure.api.routers.offboarding_tasks import router as tasks_router
from app.infrastructure.api.schemas.common import ErrorResponse
from app.infrastructure.api.schemas.offboarding import (
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
router.include_router(tasks_router)

_404 = {
    404:
        {
            "model": ErrorResponse,
            "description": "Process not found"
        }
}


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
        employee_id: Annotated[
            str | None, Query(description="Filter by employee ID (Slack user ID)")
        ] = None,
        manager_id: Annotated[
            str | None, Query(description="Filter by manager ID (Slack user ID)")
        ] = None,
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
