"""HTTP endpoints for SOP (Standard Operating Procedure) management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.application.service_interfaces.sop_service_interface import ISopService
from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.api.dependencies import sop_service_dependency
from app.infrastructure.api.schemas.common import ErrorResponse
from app.infrastructure.api.schemas.sop import (
    CreateSopRequest,
    SopPageResponse,
    SopResponse,
    UpdateSopRequest,
    sop_page_response,
    sop_to_response,
)

router = APIRouter(
    prefix="/sops",
    tags=["sops"],
    dependencies=[Depends(get_current_service)],
)

_404 = {404: {"model": ErrorResponse, "description": "SOP not found"}}


@router.post(
    "",
    response_model=SopResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new SOP",
)
async def create_sop(
        body: CreateSopRequest,
        service: Annotated[ISopService, Depends(sop_service_dependency)],
) -> SopResponse:
    """Create a new SOP, publishing SOPCreated."""
    sop = await service.create_sop(
        content=body.content,
        author=AuthorId(body.author),
        origin_channel=ChannelId(body.origin_channel),
        tags=body.tags,
    )
    return sop_to_response(sop)


@router.get(
    "",
    response_model=SopPageResponse,
    summary="Search SOPs by text and/or tags, paginated",
)
async def search_sops(
        service: Annotated[ISopService, Depends(sop_service_dependency)],
        q: Annotated[str | None, Query(description="Free-text search over SOP content")] = None,
        tags: Annotated[
            list[str] | None,
            Query(description="Tags a SOP must ALL have (repeat for multiple)"),
        ] = None,
        page: Annotated[int, Query(ge=1, description="1-indexed page number")] = 1,
        size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> SopPageResponse:
    """Search non-deleted SOPs, optionally filtered by text and/or tags."""
    sops, total = await service.search_sops(text=q, tags=tags, page=page, size=size)
    return sop_page_response(sops, page=page, size=size, total=total)


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


@router.patch(
    "/{sop_id}",
    response_model=SopResponse,
    responses=_404,
    summary="Partially update a SOP (bumps its version)",
)
async def update_sop(
        sop_id: UUID,
        body: UpdateSopRequest,
        service: Annotated[ISopService, Depends(sop_service_dependency)],
) -> SopResponse:
    """Apply a partial revision to a SOP, incrementing its version."""
    sop = await service.update_sop(SopId(sop_id), content=body.content, tags=body.tags)
    return sop_to_response(sop)


@router.delete(
    "/{sop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_404,
    summary="Soft-delete a SOP",
)
async def delete_sop(
        sop_id: UUID,
        service: Annotated[ISopService, Depends(sop_service_dependency)],
) -> None:
    """Soft-delete a SOP by its ID."""
    await service.delete_sop(SopId(sop_id))
