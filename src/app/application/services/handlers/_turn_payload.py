"""Shared helper for handlers that receive raw interview turn dicts over Kafka."""

from datetime import datetime

from app.domain import InterviewNote, InterviewQuestion, InterviewTurn, SpeakerRoleEnum


def turn_from_payload(raw: dict) -> InterviewTurn:
    """Convert a raw turn dict (Kafka payload shape) into a domain InterviewTurn.

    Mirrors InterviewTurnRequest.to_domain (the REST equivalent) since the
    Kafka payload uses the same field names. Shared by InterviewCompletedHandler
    (SA-16: full turn-list replace) and InterviewTurnRecordedHandler (SA-16:
    incremental per-turn append).

    Args:
        raw: The raw turn dict, e.g. {"turn_type": "question", "speaker_role": ..., ...}.

    Returns:
        The corresponding InterviewQuestion or InterviewNote.
    """
    role = SpeakerRoleEnum(raw["speaker_role"])
    common = {
        "speaker_role": role,
        "timestamp": datetime.fromisoformat(raw["timestamp"]),
        "content": raw["content"],
        "order": raw["order"],
        "topic": raw.get("topic"),
        "sentiment": raw.get("sentiment"),
    }
    if raw["turn_type"] == "question":
        return InterviewQuestion(**common, answer_text=raw.get("answer_text"))
    return InterviewNote(**common)
