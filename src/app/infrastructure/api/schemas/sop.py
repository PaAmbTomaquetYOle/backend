"""Request/response schemas for SOP endpoints."""

import math
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.sops.sop import Sop


class CreateSopRequest(BaseModel):
    """Request body for creating a new SOP."""

    content: str
    author: str
    origin_channel: str
    tags: list[str] = []


class UpdateSopRequest(BaseModel):
    """Request body for partially updating a SOP. Omitted fields are unchanged."""

    content: str | None = None
    tags: list[str] | None = None


class SopResponse(BaseModel):
    """Response body representing a SOP."""

    id: UUID
    content: str
    author: str
    tags: list[str]
    origin_channel: str
    version: int
    created_at: datetime
    updated_at: datetime


def sop_to_response(sop: Sop) -> SopResponse:
    """Convert a domain Sop to its API response schema.

    Args:
        sop: The domain aggregate to serialize.

    Returns:
        SopResponse: The corresponding response schema.
    """
    return SopResponse(
        id=sop.sop_id.get_id(),
        content=sop.content,
        author=sop.author.get_id(),
        tags=sop.tags,
        origin_channel=sop.origin_channel.get_id(),
        version=sop.version,
        created_at=sop.created_at,
        updated_at=sop.updated_at,
    )


class SopPageResponse(BaseModel):
    """Paginated list response for SOPs."""

    items: list[SopResponse]
    page: int
    size: int
    total: int
    total_pages: int


def sop_page_response(sops: list[Sop], page: int, size: int, total: int) -> SopPageResponse:
    """Build a paginated SOP list response.

    Args:
        sops: The page of SOPs to serialize.
        page: The 1-indexed page number requested.
        size: The page size requested.
        total: The total number of matches across all pages.

    Returns:
        SopPageResponse: The paginated response body.
    """
    total_pages = math.ceil(total / size) if size else 0
    return SopPageResponse(
        items=[sop_to_response(s) for s in sops],
        page=page,
        size=size,
        total=total,
        total_pages=total_pages,
    )
