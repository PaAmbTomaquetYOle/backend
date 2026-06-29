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
        raise InvalidInterviewStateTransitionError(self.get_state(), InterviewStateEnum.IN_PROGRESS)

    def complete(self) -> InterviewState:
        raise InvalidInterviewStateTransitionError(self.get_state(), InterviewStateEnum.COMPLETED)

    def cancel(self) -> InterviewState:
        raise InvalidInterviewStateTransitionError(self.get_state(), InterviewStateEnum.CANCELLED)
