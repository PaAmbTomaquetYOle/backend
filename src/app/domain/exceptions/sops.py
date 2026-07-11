"""Exceptions raised by the SOP domain."""

from app.domain.exceptions.base import DomainException


class SopDomainError(DomainException):
    """Base exception for SOP domain errors."""

    def __init__(self, message: str):
        """Initialize with an error message.

        Args:
            message: Human-readable description of the error.
        """
        super().__init__(message)


class SopNotFoundError(SopDomainError):
    """Raised when a SOP with the given ID does not exist (or was soft-deleted)."""

    def __init__(self, sop_id_str: str):
        """Initialize with the ID of the missing SOP.

        Args:
            sop_id_str: String representation of the SOP ID that was not found.
        """
        super().__init__(f"SOP {sop_id_str} not found")


class SopCandidateNotFoundError(SopDomainError):
    """Raised when no SOP candidate exists for the given channel/message_ts."""

    def __init__(self, channel_id_str: str, message_ts: str):
        """Initialize with the channel/message_ts of the missing candidate.

        Args:
            channel_id_str: String representation of the candidate's channel ID.
            message_ts: The Slack message timestamp identifying the candidate.
        """
        super().__init__(f"SOP candidate {channel_id_str}:{message_ts} not found")


class InvalidSopCandidateTransitionError(SopDomainError):
    """Raised when a decision is recorded for a candidate that already has one."""

    def __init__(self, current_status: str):
        """Initialize with the candidate's current status.

        Args:
            current_status: The status the candidate was already in.
        """
        super().__init__(f"SOP candidate already decided (status: {current_status})")
