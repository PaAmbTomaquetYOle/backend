"""Base exception for all domain-layer errors."""

from abc import ABC


class DomainException(RuntimeError, ABC):
    """
    Abstract base class for domain exceptions
    """