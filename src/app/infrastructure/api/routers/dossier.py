"""Top-level HTTP endpoints for cross-process dossier search."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.application.service_interfaces.dossier_service_interface import IDossierService
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.api.dependencies import dossier_service_dependency
from app.infrastructure.api.rate_limiter import limiter
from app.infrastructure.api.schemas.dossier import (
    DossierSearchListResponse,
    dossier_search_result_to_response,
)
from app.infrastructure.config.settings import get_settings

router = APIRouter(
    prefix="/dossiers",
    tags=["dossier"],
    dependencies=[Depends(get_current_service)],
)


@router.get(
    "/search",
    response_model=DossierSearchListResponse,
    summary="Search dossiers by employee name and/or process ID",
)
@limiter.limit(lambda: get_settings().rate_limit_search)
async def search_dossiers(
    request: Request,
    service: Annotated[IDossierService, Depends(dossier_service_dependency)],
    employee_name: Annotated[
        str | None, Query(description="Partial, case-insensitive employee name to search for")
    ] = None,
    process_id: Annotated[UUID | None, Query(description="Exact process UUID to filter by")] = None,
) -> DossierSearchListResponse:
    """Search offboarding dossiers by employee display name and/or associated process ID.

    At least one of employee_name or process_id must be provided.
    """
    if employee_name is None and process_id is None:
        raise HTTPException(
            status_code=422,
            detail="At least one of 'employee_name' or 'process_id' must be provided",
        )
    results = await service.search_dossiers(employee_name=employee_name, process_id=process_id)
    items = [dossier_search_result_to_response(r) for r in results]
    return DossierSearchListResponse(items=items, count=len(items))
