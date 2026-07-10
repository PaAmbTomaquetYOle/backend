"""Request/response schemas for interview endpoints."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.domain import (
    Interview,
    InterviewNote,
    InterviewQuestion,
    InterviewTurn,
    SpeakerRoleEnum,
)


class InterviewTurnRequest(BaseModel):
    """Request body for a single interview turn.

    Validates that answer_text is absent on note turns.
    """

    turn_type: Literal["question", "note"]
    speaker_role: Literal["interviewer", "interviewee"]
    timestamp: datetime
    content: str
    order: int
    topic: str | None = None
    sentiment: str | None = None
    answer_text: str | None = None

    @model_validator(mode="after")
    def validate_answer_text(self) -> Self:
        """Validate that note turns do not include answer_text."""
        if self.turn_type == "note" and self.answer_text is not None:
            raise ValueError("answer_text is only valid for turn_type 'question'")
        return self

    def to_domain(self) -> InterviewTurn:
        """Convert the request schema to a domain InterviewTurn value object.

        Returns:
            InterviewTurn: The corresponding domain value object.
        """
        role = SpeakerRoleEnum(self.speaker_role)
        if self.turn_type == "question":
            return InterviewQuestion(
                speaker_role=role,
                timestamp=self.timestamp,
                content=self.content,
                order=self.order,
                topic=self.topic,
                sentiment=self.sentiment,
                answer_text=self.answer_text,
            )
        return InterviewNote(
            speaker_role=role,
            timestamp=self.timestamp,
            content=self.content,
            order=self.order,
            topic=self.topic,
            sentiment=self.sentiment,
        )


class UpsertInterviewRequest(BaseModel):
    """Request body for creating or replacing an interview."""

    scheduled_at: datetime
    turns: list[InterviewTurnRequest] = []


class AddTurnsRequest(BaseModel):
    """Request body for appending turns to an existing interview."""

    turns: list[InterviewTurnRequest]


class InterviewTurnResponse(BaseModel):
    """Response body representing a single interview turn."""

    turn_type: str
    speaker_role: str
    timestamp: datetime
    content: str
    order: int
    topic: str | None
    sentiment: str | None
    answer_text: str | None


class InterviewResponse(BaseModel):
    """Response body representing an interview."""

    id: UUID
    process_id: UUID
    state: str
    scheduled_at: datetime
    created_at: datetime
    turns: list[InterviewTurnResponse]


def _turn_to_response(turn: InterviewTurn) -> InterviewTurnResponse:
    """Convert a domain InterviewTurn to its API response schema.

    Args:
        turn: The domain turn value object to serialize.

    Returns:
        InterviewTurnResponse: The corresponding response schema.
    """
    answer_text = turn.answer_text if isinstance(turn, InterviewQuestion) else None
    return InterviewTurnResponse(
        turn_type=turn.get_turn_type(),
        speaker_role=turn.speaker_role.value,
        timestamp=turn.timestamp,
        content=turn.content,
        order=turn.order,
        topic=turn.topic,
        sentiment=turn.sentiment,
        answer_text=answer_text,
    )


def interview_to_response(interview: Interview) -> InterviewResponse:
    """Convert a domain Interview to its API response schema.

    Args:
        interview: The domain aggregate to serialize.

    Returns:
        InterviewResponse: The corresponding response schema.
    """
    return InterviewResponse(
        id=interview.interview_id.get_id(),
        process_id=interview.process_id.get_id(),
        state=interview.state.get_state().value,
        scheduled_at=interview.scheduled_at,
        created_at=interview.created_at,
        turns=[_turn_to_response(t) for t in interview.turns],
    )
