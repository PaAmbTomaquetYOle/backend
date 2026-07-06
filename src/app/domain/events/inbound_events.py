"""Event types the backend consumes from slack-agent.

These are plain ``event_type`` string constants (not DomainEvent factories,
since the backend does not construct these events — it only recognizes and
deserializes them). They double as the dispatch keys for
``InboundEventDispatcher``.
"""

OFFBOARDING_TRIGGERED = "offboarding.triggered"
INTERVIEW_COMPLETED = "interview.completed"
DOSSIER_GENERATION_REQUESTED = "dossier.generation_requested"

INBOUND_EVENT_TYPES = (
    OFFBOARDING_TRIGGERED,
    INTERVIEW_COMPLETED,
    DOSSIER_GENERATION_REQUESTED,
)
