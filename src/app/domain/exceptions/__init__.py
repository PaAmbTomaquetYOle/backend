"""Domain exceptions package.

This package contains the base exception type and any domain-specific
exceptions raised by the domain layer.
"""

from base import DomainException
from invalid_state_transition import (
    InvalidOffboardingProcessStateTransitionError,
    InvalidStateTransitionError,
)

__all__ = [
    "DomainException",
    "InvalidOffboardingProcessStateTransitionError",
    "InvalidStateTransitionError",
]