"""HTTP endpoints for the tasks extracted for an offboarding process (SA-18).

Writes (persisting extracted tasks) are Kafka-only — see
``domain/events/inbound_events.py`` — this router is read-only.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.service_interfaces.offboarding_task_service_interface import (
    IOffboardingTaskService,
)
from app.domain import OffboardingProcessId
from app.infrastructure.api.dependencies import task_service_dependency
from app.infrastructure.api.schemas.offboarding_task import (
    OffboardingTaskListResponse,
    task_to_response,
)

router = APIRouter(tags=["tasks"])


@router.get(
    "/{process_id}/tasks",
    response_model=OffboardingTaskListResponse,
    summary="List tasks extracted for an offboarding process",
)
async def get_tasks(
        process_id: UUID,
        service: Annotated[IOffboardingTaskService, Depends(task_service_dependency)],
) -> OffboardingTaskListResponse:
    """Retrieve the Jira/Trello tasks extracted for an offboarding process."""
    tasks = await service.list_for_process(OffboardingProcessId(process_id))
    return OffboardingTaskListResponse(items=[task_to_response(t) for t in tasks])
