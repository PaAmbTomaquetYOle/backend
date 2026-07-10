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
