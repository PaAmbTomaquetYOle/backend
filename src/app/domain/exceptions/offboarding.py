"""Exceptions raised by the offboarding process domain."""

from app.domain.exceptions.base import DomainException


class OffboardingDomainError(DomainException):
    """Base exception for offboarding process domain errors."""

    def __init__(self, message: str):
        """Initialize with an error message.

        Args:
            message: Human-readable description of the error.
        """
        super().__init__(message)


class ProcessNotFoundError(OffboardingDomainError):
    """Raised when an offboarding process with the given ID does not exist."""

    def __init__(self, process_id_str: str):
        """Initialize with the ID of the missing process.

        Args:
            process_id_str: String representation of the process ID that was not found.
        """
        super().__init__(f"Offboarding process {process_id_str} not found")
