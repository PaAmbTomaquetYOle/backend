"""Exceptions raised by the interview domain."""

from app.domain.exceptions.base import DomainException


class InterviewDomainError(DomainException):
    """Base exception for Interview domain errors."""

    def __init__(self, message: str):
        """Initialize with an error message.

        Args:
            message: Human-readable description of the error.
        """
        super().__init__(message)


class InterviewAlreadyExistsForProcessError(InterviewDomainError):
    """Raised when trying to create a second interview for a process (1:1 constraint)."""

    def __init__(self, process_id_str: str):
        """Initialize with the ID of the process that already has an interview.

        Args:
            process_id_str: String representation of the process ID.
        """
        super().__init__(f"An interview already exists for process {process_id_str}")


class InterviewTurnOrderError(InterviewDomainError):
    """Raised when an invalid turn order is provided."""

    def __init__(self, message: str):
        """Initialize with a description of the ordering violation.

        Args:
            message: Human-readable description of the turn order error.
        """
        super().__init__(message)


class InterviewNotInProgressError(InterviewDomainError):
    """Raised when trying to add turns to an interview that is not in progress."""

    def __init__(self):
        """Initialize with a fixed message."""
        super().__init__("Cannot add turns: interview is not in progress")


class InterviewNotFoundError(InterviewDomainError):
    """Raised when an interview for the given process does not exist."""

    def __init__(self, detail: str = "Interview not found"):
        """Initialize with an optional detail message.

        Args:
            detail: Human-readable description. Defaults to "Interview not found".
        """
        super().__init__(detail)
