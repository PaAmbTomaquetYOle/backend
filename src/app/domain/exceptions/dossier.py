"""Exceptions raised by the dossier domain."""

from app.domain.exceptions.base import DomainException


class DossierDomainError(DomainException):
    """Base exception for Dossier domain errors."""

    def __init__(self, message: str):
        """Initialize with an error message.

        Args:
            message: Human-readable description of the error.
        """
        super().__init__(message)


class DossierInterviewNotCompletedError(DossierDomainError):
    """Raised when trying to generate a dossier before the interview is completed."""

    def __init__(self):
        """Initialize with a fixed message."""
        super().__init__("Cannot generate dossier: interview is not completed")


class DossierAlreadyExistsForProcessError(DossierDomainError):
    """Raised when trying to create a second dossier for a process."""

    def __init__(self, process_id_str: str):
        """Initialize with the ID of the process that already has a dossier.

        Args:
            process_id_str: String representation of the process ID.
        """
        super().__init__(f"A dossier already exists for process {process_id_str}")


class DossierSectionError(DossierDomainError):
    """Raised for section-related validation errors."""

    def __init__(self, message: str):
        """Initialize with a description of the section validation failure.

        Args:
            message: Human-readable description of the section error.
        """
        super().__init__(message)


class DossierNotFoundError(DossierDomainError):
    """Raised when a dossier for the given process does not exist."""

    def __init__(self, detail: str = "Dossier not found"):
        """Initialize with an optional detail message.

        Args:
            detail: Human-readable description. Defaults to "Dossier not found".
        """
        super().__init__(detail)
