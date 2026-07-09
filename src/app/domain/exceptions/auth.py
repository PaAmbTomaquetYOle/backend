"""Exceptions raised by the service-to-service authentication domain."""

from app.domain.exceptions.base import DomainException


class AuthDomainError(DomainException):
    """Base exception for authentication domain errors."""

    def __init__(self, message: str):
        """Initialize with an error message.

        Args:
            message: Human-readable description of the error.
        """
        super().__init__(message)


class InvalidCredentialsError(AuthDomainError):
    """Raised when a client_id/client_secret pair fails verification."""

    def __init__(self):
        """Initialize with a fixed, non-enumerating error message."""
        super().__init__("Invalid client credentials")
