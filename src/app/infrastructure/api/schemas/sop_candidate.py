"""Response schemas for SOP candidate endpoints (SA-16, read-only)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.sops.candidate import SopCandidate


class SopCandidateResponse(BaseModel):
    """Response body representing a SOP candidate awaiting a decision."""

    id: UUID
    channel_id: str
    author_id: str
    message_ts: str
    content: str
    status: str
    created_at: datetime
    updated_at: datetime


def sop_candidate_to_response(candidate: SopCandidate) -> SopCandidateResponse:
    """Convert a domain SopCandidate to its API response schema.

    Args:
        candidate: The domain aggregate to serialize.

    Returns:
        SopCandidateResponse: The corresponding response schema.
    """
    return SopCandidateResponse(
        id=candidate.candidate_id.get_id(),
        channel_id=candidate.channel_id.get_id(),
        author_id=candidate.author_id.get_id(),
        message_ts=candidate.message_ts,
        content=candidate.content,
        status=candidate.status.value,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
    )


class SopCandidateListResponse(BaseModel):
    """List response for pending SOP candidates."""

    items: list[SopCandidateResponse]
