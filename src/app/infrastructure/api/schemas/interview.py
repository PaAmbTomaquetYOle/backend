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
        if self.turn_type == "note" and self.answer_text is not None:
            raise ValueError("answer_text is only valid for turn_type 'question'")
        return self

    def to_domain(self) -> InterviewTurn:
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
    scheduled_at: datetime
    turns: list[InterviewTurnRequest] = []


class AddTurnsRequest(BaseModel):
    turns: list[InterviewTurnRequest]


class InterviewTurnResponse(BaseModel):
    turn_type: str
    speaker_role: str
    timestamp: datetime
    content: str
    order: int
    topic: str | None
    sentiment: str | None
    answer_text: str | None


class InterviewResponse(BaseModel):
    id: UUID
    process_id: UUID
    state: str
    scheduled_at: datetime
    created_at: datetime
    turns: list[InterviewTurnResponse]


def _turn_to_response(turn: InterviewTurn) -> InterviewTurnResponse:
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
    return InterviewResponse(
        id=interview.interview_id.get_id(),
        process_id=interview.process_id.get_id(),
        state=interview.state.get_state().value,
        scheduled_at=interview.scheduled_at,
        created_at=interview.created_at,
        turns=[_turn_to_response(t) for t in interview.turns],
    )
