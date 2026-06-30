"""Interview aggregate root."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.enums import InterviewStateEnum
from app.domain.exceptions.interview import InterviewNotInProgressError

if TYPE_CHECKING:
    from app.domain.interview.state.base import InterviewState
    from app.domain.interview.turn import InterviewTurn
    from app.domain.offboarding.id import InterviewId, ProcessId


class Interview:
    """Interview aggregate root. 1:1 with OffboardingProcess."""

    def __init__(
        self,
        interview_id: InterviewId,
        process_id: ProcessId,
        state: InterviewState,
        scheduled_at: datetime,
        created_at: datetime,
        turns: list[InterviewTurn] | None = None,
    ) -> None:
        """Initialize the interview with its identifying attributes.

        Args:
            interview_id: Unique identifier for this interview.
            process_id: ID of the offboarding process this interview belongs to.
            state: Initial state of the interview (typically ScheduledInterviewState).
            scheduled_at: When the interview is scheduled to take place.
            created_at: Timestamp when the interview record was created.
            turns: Pre-existing conversation turns. Defaults to an empty list.
        """
        self.__id = interview_id
        self.__process_id = process_id
        self.__state = state
        self.__scheduled_at = scheduled_at
        self.__created_at = created_at
        self.__turns: list[InterviewTurn] = turns if turns is not None else []

    @property
    def interview_id(self) -> InterviewId:
        """The unique identifier of this interview."""
        return self.__id

    @property
    def process_id(self) -> ProcessId:
        """The ID of the offboarding process this interview is associated with."""
        return self.__process_id

    @property
    def state(self) -> InterviewState:
        """The current state object of this interview."""
        return self.__state

    @property
    def scheduled_at(self) -> datetime:
        """When the interview is scheduled to take place."""
        return self.__scheduled_at

    @scheduled_at.setter
    def scheduled_at(self, value: datetime) -> None:
        """Set or update the scheduled time of the interview."""
        self.__scheduled_at = value

    @property
    def created_at(self) -> datetime:
        """Timestamp when the interview record was created."""
        return self.__created_at

    @property
    def turns(self) -> list[InterviewTurn]:
        """A copy of the conversation turns recorded in this interview."""
        return list(self.__turns)

    def start(self) -> InterviewState:
        """Transition to IN_PROGRESS. Raises InvalidInterviewStateTransitionError if invalid."""
        new_state = self.__state.start()
        self.__state = new_state
        return new_state

    def complete(self) -> InterviewState:
        """Transition to COMPLETED. Raises InvalidInterviewStateTransitionError if invalid."""
        new_state = self.__state.complete()
        self.__state = new_state
        return new_state

    def cancel(self) -> InterviewState:
        """Transition to CANCELLED. Raises InvalidInterviewStateTransitionError if invalid."""
        new_state = self.__state.cancel()
        self.__state = new_state
        return new_state

    def add_turn(self, turn: InterviewTurn) -> None:
        """Add a turn to the interview. Interview must be IN_PROGRESS."""
        if self.__state.get_state() != InterviewStateEnum.IN_PROGRESS:
            raise InterviewNotInProgressError()
        self.__turns.append(turn)
