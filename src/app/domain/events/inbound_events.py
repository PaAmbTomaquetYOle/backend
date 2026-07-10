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
DOSSIER_GENERATION_REQUESTED = "dossier.generation_requested"
SOP_CREATION_REQUESTED = "sop.creation_requested"
KNOWLEDGE_INTERACTION_REGISTERED = "knowledge_graph.interaction_registered"
KNOWLEDGE_DOCUMENT_REGISTERED = "knowledge_graph.document_registered"
KNOWLEDGE_CHANNEL_ACTIVITY_REGISTERED = "knowledge_graph.channel_activity_registered"

INBOUND_EVENT_TYPES = (
    OFFBOARDING_TRIGGERED,
    OFFBOARDING_CANCELLATION_REQUESTED,
    INTERVIEW_STARTED,
    INTERVIEW_COMPLETED,
    DOSSIER_GENERATION_REQUESTED,
    SOP_CREATION_REQUESTED,
    KNOWLEDGE_INTERACTION_REGISTERED,
    KNOWLEDGE_DOCUMENT_REGISTERED,
    KNOWLEDGE_CHANNEL_ACTIVITY_REGISTERED,
)
