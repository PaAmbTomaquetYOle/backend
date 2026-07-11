"""SopCandidate aggregate root — a message flagged as a possible SOP, awaiting a decision.

Like Sop, a SopCandidate has no branching lifecycle state machine (State
pattern) — just a small linear status with a single guarded transition
(offered -> accepted | rejected), so it is modeled as a plain enum guard
rather than a state/ subpackage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.domain.enums import SopCandidateStatus
from app.domain.exceptions.sops import InvalidSopCandidateTransitionError

if TYPE_CHECKING:
    from app.domain.sops.id import AuthorId, ChannelId, SopCandidateId


class SopCandidate:
    """A Slack message offered to its author as a possible SOP, pending their decision.

    Persisted from the moment it is offered (SA-16) so that a slack-agent
    restart before the author responds doesn't lose the candidate — the
    author's eventual Yes/No click can still be resolved.
    """

    __candidate_id: SopCandidateId
    __channel_id: ChannelId
    __author_id: AuthorId
    __message_ts: str
    __content: str
    __status: SopCandidateStatus
    __created_at: datetime
    __updated_at: datetime

    def __init__(
            self,
            candidate_id: SopCandidateId,
            channel_id: ChannelId,
            author_id: AuthorId,
            message_ts: str,
            content: str,
            created_at: datetime,
            status: SopCandidateStatus = SopCandidateStatus.OFFERED,
            updated_at: datetime | None = None,
    ) -> None:
        """Initialize the candidate with all its attributes.

        Args:
            candidate_id: Unique identifier for this candidate.
            channel_id: Identifier of the Slack channel the message was posted in.
            author_id: Identifier of the Slack user who authored the message.
            message_ts: The Slack message timestamp, unique within its channel.
            content: The message text offered as a possible SOP.
            created_at: Timestamp when the candidate was first persisted (offered).
            status: Current decision status. Defaults to OFFERED.
            updated_at: Timestamp of the last status change. Defaults to created_at.
        """
        self.__candidate_id = candidate_id
        self.__channel_id = channel_id
        self.__author_id = author_id
        self.__message_ts = message_ts
        self.__content = content
        self.__created_at = created_at
        self.__status = status
        self.__updated_at = updated_at or created_at

    @property
    def candidate_id(self) -> SopCandidateId:
        """The unique identifier of this candidate."""
        return self.__candidate_id

    @property
    def channel_id(self) -> ChannelId:
        """The Slack channel the candidate message was posted in."""
        return self.__channel_id

    @property
    def author_id(self) -> AuthorId:
        """The Slack user who authored the candidate message."""
        return self.__author_id

    @property
    def message_ts(self) -> str:
        """The Slack message timestamp identifying the source message."""
        return self.__message_ts

    @property
    def content(self) -> str:
        """The message text offered as a possible SOP."""
        return self.__content

    @property
    def status(self) -> SopCandidateStatus:
        """The current decision status."""
        return self.__status

    @property
    def created_at(self) -> datetime:
        """Timestamp when the candidate was first persisted (offered)."""
        return self.__created_at

    @property
    def updated_at(self) -> datetime:
        """Timestamp of the last status change."""
        return self.__updated_at

    @property
    def is_pending(self) -> bool:
        """Whether the candidate is still awaiting a decision."""
        return self.__status == SopCandidateStatus.OFFERED

    def mark_accepted(self) -> None:
        """Record that the author accepted turning this candidate into a SOP.

        Raises:
            InvalidSopCandidateTransitionError: If a decision was already recorded.
        """
        self.__transition_to(SopCandidateStatus.ACCEPTED)

    def mark_rejected(self) -> None:
        """Record that the author declined turning this candidate into a SOP.

        Raises:
            InvalidSopCandidateTransitionError: If a decision was already recorded.
        """
        self.__transition_to(SopCandidateStatus.REJECTED)

    def __transition_to(self, status: SopCandidateStatus) -> None:
        if not self.is_pending:
            raise InvalidSopCandidateTransitionError(self.__status.value)
        self.__status = status
        self.__updated_at = datetime.now(timezone.utc)
