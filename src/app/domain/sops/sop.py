"""Sop aggregate root — a knowledge document, not a lifecycle process."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.sops.id import AuthorId, ChannelId, SopId


class Sop:
    """Aggregate root representing a Standard Operating Procedure.

    Unlike OffboardingProcess, a Sop has no lifecycle state machine: it is a
    versioned knowledge document that can be revised or soft-deleted.
    """

    __sop_id: SopId
    __content: str
    __author: AuthorId
    __tags: list[str]
    __origin_channel: ChannelId
    __version: int
    __created_at: datetime
    __updated_at: datetime
    __deleted_at: datetime | None

    def __init__(
            self,
            sop_id: SopId,
            content: str,
            author: AuthorId,
            tags: list[str],
            origin_channel: ChannelId,
            created_at: datetime,
            version: int = 1,
            updated_at: datetime | None = None,
            deleted_at: datetime | None = None,
    ) -> None:
        """Initialize the SOP with all its attributes.

        Args:
            sop_id: Unique identifier for this SOP.
            content: The operational knowledge text.
            author: Identifier of the Slack user who authored the SOP.
            tags: Free-form categorization tags.
            origin_channel: Identifier of the Slack channel the SOP originated from.
            created_at: Timestamp when the SOP was created.
            version: Revision counter, starting at 1. Defaults to 1.
            updated_at: Timestamp of the last revision. Defaults to created_at.
            deleted_at: Timestamp when the SOP was soft-deleted, or None if active.
        """
        self.__sop_id = sop_id
        self.__content = content
        self.__author = author
        self.__tags = list(tags)
        self.__origin_channel = origin_channel
        self.__created_at = created_at
        self.__version = version
        self.__updated_at = updated_at or created_at
        self.__deleted_at = deleted_at

    @property
    def sop_id(self) -> SopId:
        """The unique identifier of this SOP."""
        return self.__sop_id

    @property
    def content(self) -> str:
        """The operational knowledge text."""
        return self.__content

    @property
    def author(self) -> AuthorId:
        """The Slack user who authored the SOP."""
        return self.__author

    @property
    def tags(self) -> list[str]:
        """The categorization tags attached to this SOP."""
        return list(self.__tags)

    @property
    def origin_channel(self) -> ChannelId:
        """The Slack channel this SOP originated from."""
        return self.__origin_channel

    @property
    def version(self) -> int:
        """The current revision number, starting at 1."""
        return self.__version

    @property
    def created_at(self) -> datetime:
        """Timestamp when the SOP was created."""
        return self.__created_at

    @property
    def updated_at(self) -> datetime:
        """Timestamp of the last revision."""
        return self.__updated_at

    @property
    def deleted_at(self) -> datetime | None:
        """Timestamp when the SOP was soft-deleted, or None if still active."""
        return self.__deleted_at

    @property
    def is_deleted(self) -> bool:
        """Whether this SOP has been soft-deleted."""
        return self.__deleted_at is not None

    def revise(self, content: str | None = None, tags: list[str] | None = None) -> None:
        """Apply a partial revision to the SOP, bumping its version.

        Only the fields provided are changed; omitted fields keep their
        current value. Always increments ``version`` and refreshes
        ``updated_at``.

        Args:
            content: New content, if being changed. Defaults to None (unchanged).
            tags: New tag list, if being changed. Defaults to None (unchanged).
        """
        if content is not None:
            self.__content = content
        if tags is not None:
            self.__tags = list(tags)
        self.__version += 1
        self.__updated_at = datetime.now(timezone.utc)

    def mark_deleted(self) -> None:
        """Soft-delete the SOP by setting its deleted_at timestamp."""
        self.__deleted_at = datetime.now(timezone.utc)
