from abc import ABC


class DomainException(RuntimeError, ABC):
    """
    Abstract base class for domain exceptions
    """