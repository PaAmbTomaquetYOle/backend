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
