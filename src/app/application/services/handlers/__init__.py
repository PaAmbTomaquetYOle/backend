"""Inbound Kafka event handlers, one per event_type consumed from slack-agent."""

from app.application.services.handlers.dossier_generation_requested_handler import (
    DossierGenerationRequestedHandler,
)
from app.application.services.handlers.interview_completed_handler import (
    InterviewCompletedHandler,
)
from app.application.services.handlers.offboarding_triggered_handler import (
    OffboardingTriggeredHandler,
)
from app.application.services.handlers.sop_creation_requested_handler import (
    SopCreationRequestedHandler,
)

__all__ = [
    "DossierGenerationRequestedHandler",
    "InterviewCompletedHandler",
    "OffboardingTriggeredHandler",
    "SopCreationRequestedHandler",
]
