from .base import DomainEvent
from .offboarding_events import (
    DossierGenerated,
    InterviewCompleted,
    OffboardingCompleted,
    OffboardingStateChanged,
)

__all__ = [
    "DomainEvent",
    "DossierGenerated",
    "InterviewCompleted",
    "OffboardingCompleted",
    "OffboardingStateChanged",
]
