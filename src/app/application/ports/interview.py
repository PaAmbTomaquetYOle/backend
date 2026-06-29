"""Repository port interface for Interview."""

from abc import ABC, abstractmethod

from app.domain.interview.interview import Interview
from app.domain.offboarding.id import InterviewId, OffboardingProcessId


class IInterviewRepository(ABC):
    """Interface for the Interview repository."""

    @abstractmethod
    def save(self, interview: Interview) -> None:
        """Persist an interview (insert or update by ID)."""

    @abstractmethod
    def find_by_id(self, interview_id: InterviewId) -> Interview | None:
        """Return the interview with the given ID, or None if not found."""

    @abstractmethod
    def find_by_process_id(self, process_id: OffboardingProcessId) -> Interview | None:
        """Return the interview for the given process, or None if not found. 1:1 cardinality."""

    @abstractmethod
    def find_all(self) -> list[Interview]:
        """Return all stored interviews."""

    @abstractmethod
    def delete(self, interview_id: InterviewId) -> None:
        """Remove the interview with the given ID (no-op if not found)."""
