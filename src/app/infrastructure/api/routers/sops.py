"""HTTP endpoints for SOP (Standard Operating Procedure) management.

The full SOP write lifecycle (creation, update, soft-delete) is Kafka-only —
``sop.creation_requested``, ``sop.update_requested``, ``sop.deletion_requested``
(see ``domain/events/inbound_events.py``). This router only exposes read
endpoints, matching the "REST is read-only" policy.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.application.service_interfaces.sop_service_interface import ISopService
from app.domain.sops.id import SopId
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.api.dependencies import sop_service_dependency
from app.infrastructure.api.rate_limiter import limiter
from app.infrastructure.api.schemas.common import ErrorResponse
from app.infrastructure.api.schemas.sop import (
    SopPageResponse,
    SopResponse,
    sop_page_response,
    sop_to_response,
)
from app.infrastructure.config.settings import get_settings

router = APIRouter(
    prefix="/sops",
    tags=["sops"],
    dependencies=[Depends(get_current_service)],
)

_404 = {404: {"model": ErrorResponse, "description": "SOP not found"}}


@router.get(
    "",
    response_model=SopPageResponse,
    summary="Search SOPs by text and/or tags, paginated",
)
@limiter.limit(lambda: get_settings().rate_limit_search)
async def search_sops(
    request: Request,
    service: Annotated[ISopService, Depends(sop_service_dependency)],
    q: Annotated[
        str | None,
        Query(description="Free-text search over SOP title and content, ranked by relevance"),
    ] = None,
    tags: Annotated[
        list[str] | None,
        Query(description="Tags a SOP must ALL have (repeat for multiple)"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="1-indexed page number")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> SopPageResponse:
    """Search non-deleted SOPs, optionally filtered by text and/or tags."""
    hits, total = await service.search_sops(text=q, tags=tags, page=page, size=size)
    return sop_page_response(hits, page=page, size=size, total=total)


@router.get(
    "/{sop_id}",
    response_model=SopResponse,
    responses=_404,
    summary="Get a SOP by ID",
)
async def get_sop(
    sop_id: UUID,
    service: Annotated[ISopService, Depends(sop_service_dependency)],
) -> SopResponse:
    """Retrieve a specific SOP by its ID."""
    sop = await service.get_sop(SopId(sop_id))
    return sop_to_response(sop)
