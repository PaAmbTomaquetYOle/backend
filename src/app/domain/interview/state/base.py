"""Abstract base state for the Interview state machine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.enums import InterviewStateEnum
from app.domain.exceptions import InvalidInterviewStateTransitionError


class InterviewState(ABC):
    """Abstract base class for interview states."""

    @abstractmethod
    def get_state(self) -> InterviewStateEnum:
        """Returns the current interview state."""

    def start(self) -> InterviewState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidInterviewStateTransitionError: Always, since the current state
                does not support starting.
        """
        raise InvalidInterviewStateTransitionError(self.get_state(), InterviewStateEnum.IN_PROGRESS)

    def complete(self) -> InterviewState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidInterviewStateTransitionError: Always, since the current state
                does not support completing.
        """
        raise InvalidInterviewStateTransitionError(self.get_state(), InterviewStateEnum.COMPLETED)

    def cancel(self) -> InterviewState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidInterviewStateTransitionError: Always, since the current state
                does not support cancellation.
        """
        raise InvalidInterviewStateTransitionError(self.get_state(), InterviewStateEnum.CANCELLED)
