"""SQLModel persistence model for interviews."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, ForeignKey
from sqlmodel import Field, SQLModel

from app.domain.enums import InterviewStateEnum, SpeakerRoleEnum
from app.domain.interview.interview import Interview
from app.domain.interview.state.base import InterviewState
from app.domain.interview.state.cancelled import CancelledInterviewState
from app.domain.interview.state.completed import CompletedInterviewState
from app.domain.interview.state.in_progress import InProgressInterviewState
from app.domain.interview.state.scheduled import ScheduledInterviewState
from app.domain.interview.turn import InterviewNote, InterviewQuestion, InterviewTurn
from app.domain.offboarding.id import InterviewId, ProcessId

_INTERVIEW_STATE_FACTORIES: dict[str, type[InterviewState]] = {
    InterviewStateEnum.SCHEDULED.value: ScheduledInterviewState,
    InterviewStateEnum.IN_PROGRESS.value: InProgressInterviewState,
    InterviewStateEnum.COMPLETED.value: CompletedInterviewState,
    InterviewStateEnum.CANCELLED.value: CancelledInterviewState,
}

_TURN_FACTORIES: dict[str, type] = {
    "question": InterviewQuestion,
    "note": InterviewNote,
}


class InterviewModel(SQLModel, table=True):
    __tablename__ = "interviews"
    __table_args__ = (
        CheckConstraint(
            "state IN ('scheduled','in_progress','completed','cancelled')",
            name="ck_interviews_state",
        ),
    )

    id: uuid.UUID = Field(primary_key=True)
    process_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("processes.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        )
    )
    state: str = Field(nullable=False)
    scheduled_at: datetime = Field(nullable=False)
    created_at: datetime = Field(nullable=False)

    @classmethod
    def from_domain(cls, interview: Interview) -> InterviewModel:
        return cls(
            id=interview.interview_id.get_id(),
            process_id=interview.process_id.get_id(),
            state=interview.state.get_state().value,
            scheduled_at=interview.scheduled_at,
            created_at=interview.created_at,
        )

    def to_domain(self, turns: list[InterviewTurnModel] | None = None) -> Interview:
        state = _INTERVIEW_STATE_FACTORIES[self.state]()
        domain_turns: list[InterviewTurn] = []
        if turns:
            for t in sorted(turns, key=lambda x: x.turn_order):
                domain_turns.append(t.to_domain())
        return Interview(
            interview_id=InterviewId(self.id),
            process_id=ProcessId(self.process_id),
            state=state,
            scheduled_at=self.scheduled_at,
            created_at=self.created_at,
            turns=domain_turns,
        )


class InterviewTurnModel(SQLModel, table=True):
    __tablename__ = "interview_turns"
    __table_args__ = (
        sa.UniqueConstraint(
            "interview_id", "turn_order", name="uq_interview_turns_interview_order"
        ),
        CheckConstraint(
            "turn_type IN ('question','note')",
            name="ck_interview_turns_type",
        ),
        CheckConstraint(
            "speaker_role IN ('interviewer','interviewee')",
            name="ck_interview_turns_speaker_role",
        ),
        CheckConstraint("turn_order >= 0", name="ck_interview_turns_order_positive"),
    )

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    interview_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("interviews.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    turn_type: str = Field(nullable=False)
    speaker_role: str = Field(nullable=False)
    timestamp: datetime = Field(nullable=False)
    content: str = Field(nullable=False)
    turn_order: int = Field(nullable=False)
    topic: str | None = Field(default=None)
    sentiment: str | None = Field(default=None)
    answer_text: str | None = Field(default=None)

    @classmethod
    def from_domain(
        cls, turn: InterviewTurn, interview_id: uuid.UUID
    ) -> InterviewTurnModel:
        return cls(
            interview_id=interview_id,
            turn_type=turn.get_turn_type(),
            speaker_role=turn.speaker_role.value,
            timestamp=turn.timestamp,
            content=turn.content,
            turn_order=turn.order,
            topic=turn.topic,
            sentiment=turn.sentiment,
            answer_text=turn.answer_text if isinstance(turn, InterviewQuestion) else None,
        )

    def to_domain(self) -> InterviewTurn:
        role = SpeakerRoleEnum(self.speaker_role)
        if self.turn_type == "question":
            return InterviewQuestion(
                speaker_role=role,
                timestamp=self.timestamp,
                content=self.content,
                order=self.turn_order,
                topic=self.topic,
                sentiment=self.sentiment,
                answer_text=self.answer_text,
            )
        return InterviewNote(
            speaker_role=role,
            timestamp=self.timestamp,
            content=self.content,
            order=self.turn_order,
            topic=self.topic,
            sentiment=self.sentiment,
        )
