"""Inbound Kafka event handlers, one per event_type consumed from slack-agent."""

from app.application.services.handlers.annual_review_cancellation_requested_handler import (
    AnnualReviewCancellationRequestedHandler,
)
from app.application.services.handlers.annual_review_dossier_generation_requested_handler import (
    AnnualReviewDossierGenerationRequestedHandler,
)
from app.application.services.handlers.annual_review_interview_completed_handler import (
    AnnualReviewInterviewCompletedHandler,
)
from app.application.services.handlers.annual_review_triggered_handler import (
    AnnualReviewTriggeredHandler,
)
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
from app.application.services.handlers.monthly_review_cancellation_requested_handler import (
    MonthlyReviewCancellationRequestedHandler,
)
from app.application.services.handlers.monthly_review_dossier_generation_requested_handler import (
    MonthlyReviewDossierGenerationRequestedHandler,
)
from app.application.services.handlers.monthly_review_interview_completed_handler import (
    MonthlyReviewInterviewCompletedHandler,
)
from app.application.services.handlers.monthly_review_triggered_handler import (
    MonthlyReviewTriggeredHandler,
)
from app.application.services.handlers.offboarding_cancellation_requested_handler import (
    OffboardingCancellationRequestedHandler,
)
from app.application.services.handlers.offboarding_tasks_extracted_handler import (
    OffboardingTasksExtractedHandler,
)
from app.application.services.handlers.offboarding_triggered_handler import (
    OffboardingTriggeredHandler,
)
from app.application.services.handlers.sop_candidate_decided_handler import (
    SopCandidateDecidedHandler,
)
from app.application.services.handlers.sop_candidate_offered_handler import (
    SopCandidateOfferedHandler,
)
from app.application.services.handlers.sop_creation_requested_handler import (
    SopCreationRequestedHandler,
)
from app.application.services.handlers.sop_deletion_requested_handler import (
    SopDeletionRequestedHandler,
)
from app.application.services.handlers.sop_update_requested_handler import (
    SopUpdateRequestedHandler,
)

__all__ = [
    "AnnualReviewCancellationRequestedHandler",
    "AnnualReviewDossierGenerationRequestedHandler",
    "AnnualReviewInterviewCompletedHandler",
    "AnnualReviewTriggeredHandler",
    "DossierGenerationRequestedHandler",
    "InterviewCompletedHandler",
    "InterviewStartedHandler",
    "InterviewTurnRecordedHandler",
    "KnowledgeChannelActivityRegisteredHandler",
    "KnowledgeDocumentRegisteredHandler",
    "KnowledgeInteractionRegisteredHandler",
    "MonthlyReviewCancellationRequestedHandler",
    "MonthlyReviewDossierGenerationRequestedHandler",
    "MonthlyReviewInterviewCompletedHandler",
    "MonthlyReviewTriggeredHandler",
    "OffboardingCancellationRequestedHandler",
    "OffboardingTasksExtractedHandler",
    "OffboardingTriggeredHandler",
    "SopCandidateDecidedHandler",
    "SopCandidateOfferedHandler",
    "SopCreationRequestedHandler",
    "SopDeletionRequestedHandler",
    "SopUpdateRequestedHandler",
]
