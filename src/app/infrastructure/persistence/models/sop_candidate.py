"""SQLModel persistence model for SOP candidates (SA-16)."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.domain.enums import SopCandidateStatus
from app.domain.sops.candidate import SopCandidate
from app.domain.sops.id import AuthorId, ChannelId, SopCandidateId


class SopCandidateModel(SQLModel, table=True):
    """SQLModel persistence model for a SOP candidate awaiting an author decision.

    Standalone aggregate, like SopModel — no lifecycle State pattern, just a
    small status guard. Unique on (channel_id, message_ts) since that pair is
    the natural key slack-agent already uses to identify a candidate message.
    """

    __tablename__ = "sop_candidates"
    __table_args__ = (
        sa.UniqueConstraint(
            "channel_id", "message_ts", name="uq_sop_candidates_channel_message_ts"
        ),
        sa.CheckConstraint(
            "status IN ('offered','accepted','rejected')",
            name="ck_sop_candidates_status",
        ),
    )

    id: uuid.UUID = Field(primary_key=True)
    channel_id: str = Field(nullable=False, max_length=64)
    author_id: str = Field(nullable=False, max_length=64)
    message_ts: str = Field(nullable=False, max_length=64)
    content: str = Field(nullable=False)
    status: str = Field(nullable=False, max_length=16)
    created_at: datetime = Field(nullable=False)
    updated_at: datetime = Field(nullable=False)

    @classmethod
    def from_domain(cls, candidate: SopCandidate) -> SopCandidateModel:
        """Create a SopCandidateModel from a domain SopCandidate aggregate.

        Args:
            candidate: The domain SopCandidate to persist.

        Returns:
            SopCandidateModel: The corresponding persistence model.
        """
        return cls(
            id=candidate.candidate_id.get_id(),
            channel_id=candidate.channel_id.get_id(),
            author_id=candidate.author_id.get_id(),
            message_ts=candidate.message_ts,
            content=candidate.content,
            status=candidate.status.value,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
        )

    def to_domain(self) -> SopCandidate:
        """Reconstruct a domain SopCandidate from this model.

        Returns:
            SopCandidate: The reconstructed domain aggregate.
        """
        return SopCandidate(
            candidate_id=SopCandidateId(self.id),
            channel_id=ChannelId(self.channel_id),
            author_id=AuthorId(self.author_id),
            message_ts=self.message_ts,
            content=self.content,
            status=SopCandidateStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
