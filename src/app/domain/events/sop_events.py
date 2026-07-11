from datetime import datetime
from uuid import UUID

from .base import DomainEvent


def SOPCreated(
    sop_id: UUID,
    author: str,
    origin_channel: str,
    tags: list[str],
    version: int,
    created_at: datetime,
) -> DomainEvent:
    return DomainEvent(
        event_type="sop.created",
        payload={
            "sop_id": str(sop_id),
            "author": author,
            "origin_channel": origin_channel,
            "tags": tags,
            "version": version,
            "created_at": created_at.isoformat(),
        },
    )


def SOPUpdated(
    sop_id: UUID,
    editor: str,
    origin_channel: str,
    tags: list[str],
    version: int,
    updated_at: datetime,
) -> DomainEvent:
    return DomainEvent(
        event_type="sop.updated",
        payload={
            "sop_id": str(sop_id),
            "editor": editor,
            "origin_channel": origin_channel,
            "tags": tags,
            "version": version,
            "updated_at": updated_at.isoformat(),
        },
    )


def SOPDeleted(
    sop_id: UUID,
    requester: str,
    origin_channel: str,
    deleted_at: datetime,
) -> DomainEvent:
    return DomainEvent(
        event_type="sop.deleted",
        payload={
            "sop_id": str(sop_id),
            "requester": requester,
            "origin_channel": origin_channel,
            "deleted_at": deleted_at.isoformat(),
        },
    )
