"""Inbound Kafka event handlers, one per event_type consumed from slack-agent."""

from app.application.services.handlers.dossier_generation_requested_handler import (
    DossierGenerationRequestedHandler,
)
from app.application.services.handlers.interview_completed_handler import (
    InterviewCompletedHandler,
)
from app.application.services.handlers.interview_started_handler import (
    InterviewStartedHandler,
)
from app.application.services.handlers.interview_turn_recorded_handler import (
    InterviewTurnRecordedHandler,
)
from app.application.services.handlers.knowledge_channel_activity_registered_handler import (
    KnowledgeChannelActivityRegisteredHandler,
)
from app.application.services.handlers.knowledge_document_registered_handler import (
    KnowledgeDocumentRegisteredHandler,
)
from app.application.services.handlers.knowledge_interaction_registered_handler import (
    KnowledgeInteractionRegisteredHandler,
)
from app.application.services.handlers.offboarding_cancellation_requested_handler import (
    OffboardingCancellationRequestedHandler,
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
    "InterviewStartedHandler",
    "InterviewTurnRecordedHandler",
    "KnowledgeChannelActivityRegisteredHandler",
    "KnowledgeDocumentRegisteredHandler",
    "KnowledgeInteractionRegisteredHandler",
    "OffboardingCancellationRequestedHandler",
    "OffboardingTriggeredHandler",
    "SopCreationRequestedHandler",
]
