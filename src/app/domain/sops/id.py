"""Value objects representing typed identifiers used by the SOP bounded context."""

from __future__ import annotations

from app.domain.offboarding.id import ExternalUserId, Id


class SopId(Id):
    """Class representing a SOP ID."""


class SopCandidateId(Id):
    """Class representing a SOP candidate ID."""


class AuthorId(ExternalUserId):
    """Class representing the author of a SOP (an external Slack user ID)."""


class ChannelId(ExternalUserId):
    """Class representing the origin Slack channel of a SOP."""
