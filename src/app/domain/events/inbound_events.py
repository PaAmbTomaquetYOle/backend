"""Event types the backend consumes from slack-agent.

These are plain ``event_type`` string constants (not DomainEvent factories,
since the backend does not construct these events — it only recognizes and
deserializes them). They double as the dispatch keys for
``InboundEventDispatcher``.
"""

OFFBOARDING_TRIGGERED = "offboarding.triggered"
OFFBOARDING_CANCELLATION_REQUESTED = "offboarding.cancellation_requested"
INTERVIEW_STARTED = "interview.started"
INTERVIEW_COMPLETED = "interview.completed"
INTERVIEW_TURN_RECORDED = "interview.turn_recorded"
TASKS_EXTRACTED = "tasks.extracted"
DOSSIER_GENERATION_REQUESTED = "dossier.generation_requested"
SOP_CREATION_REQUESTED = "sop.creation_requested"
SOP_UPDATE_REQUESTED = "sop.update_requested"
SOP_DELETION_REQUESTED = "sop.deletion_requested"
SOP_CANDIDATE_OFFERED = "sop.candidate_offered"
SOP_CANDIDATE_DECIDED = "sop.candidate_decided"
KNOWLEDGE_INTERACTION_REGISTERED = "knowledge_graph.interaction_registered"
KNOWLEDGE_DOCUMENT_REGISTERED = "knowledge_graph.document_registered"
KNOWLEDGE_CHANNEL_ACTIVITY_REGISTERED = "knowledge_graph.channel_activity_registered"

# BE-23: monthly/annual review processes get their own event types (not reused
# from offboarding's), since they're triggered by the backend's own scheduler
# (BE-24) rather than a Slack user command, and their interview/dossier flow
# must be dispatched independently of the offboarding one.
MONTHLY_REVIEW_TRIGGERED = "monthly_review.triggered"
MONTHLY_REVIEW_CANCELLATION_REQUESTED = "monthly_review.cancellation_requested"
MONTHLY_REVIEW_INTERVIEW_COMPLETED = "monthly_review.interview_completed"
MONTHLY_REVIEW_DOSSIER_GENERATION_REQUESTED = "monthly_review.dossier_generation_requested"
ANNUAL_REVIEW_TRIGGERED = "annual_review.triggered"
ANNUAL_REVIEW_CANCELLATION_REQUESTED = "annual_review.cancellation_requested"
ANNUAL_REVIEW_INTERVIEW_COMPLETED = "annual_review.interview_completed"
ANNUAL_REVIEW_DOSSIER_GENERATION_REQUESTED = "annual_review.dossier_generation_requested"

INBOUND_EVENT_TYPES = (
    OFFBOARDING_TRIGGERED,
    OFFBOARDING_CANCELLATION_REQUESTED,
    INTERVIEW_STARTED,
    INTERVIEW_COMPLETED,
    INTERVIEW_TURN_RECORDED,
    TASKS_EXTRACTED,
    DOSSIER_GENERATION_REQUESTED,
    SOP_CREATION_REQUESTED,
    SOP_UPDATE_REQUESTED,
    SOP_DELETION_REQUESTED,
    SOP_CANDIDATE_OFFERED,
    SOP_CANDIDATE_DECIDED,
    KNOWLEDGE_INTERACTION_REGISTERED,
    KNOWLEDGE_DOCUMENT_REGISTERED,
    KNOWLEDGE_CHANNEL_ACTIVITY_REGISTERED,
    MONTHLY_REVIEW_TRIGGERED,
    MONTHLY_REVIEW_CANCELLATION_REQUESTED,
    MONTHLY_REVIEW_INTERVIEW_COMPLETED,
    MONTHLY_REVIEW_DOSSIER_GENERATION_REQUESTED,
    ANNUAL_REVIEW_TRIGGERED,
    ANNUAL_REVIEW_CANCELLATION_REQUESTED,
    ANNUAL_REVIEW_INTERVIEW_COMPLETED,
    ANNUAL_REVIEW_DOSSIER_GENERATION_REQUESTED,
)
