"""Facade service interface for monthly review operations. Used by inbound Kafka handlers."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain import (
    Dossier,
    EmployeeId,
    Interview,
    InterviewTurn,
    ManagerId,
    MonthlyReviewProcess,
    MonthlyReviewProcessId,
    MonthlyReviewProcessStateEnum,
)


class IMonthlyReviewServiceFacade(ABC):
    """Composed facade for monthly review process, interview, and dossier operations.

    Mirrors IOffboardingServiceFacade but without submit_for_review, since
    MonthlyReviewProcess has no PENDING_REVISION state: interview completion
    leads straight into dossier generation and completion.
    """

    @abstractmethod
    async def create_review(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            employee_name: str | None = None,
            manager_name: str | None = None,
    ) -> MonthlyReviewProcess:
        """Create a new monthly review process in NOT_STARTED state."""
        ...

    @abstractmethod
    async def get_review(self, process_id: MonthlyReviewProcessId) -> MonthlyReviewProcess:
        """Retrieve a monthly review process by ID."""
        ...

    @abstractmethod
    async def list_reviews(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            state: MonthlyReviewProcessStateEnum | None = None,
    ) -> list[MonthlyReviewProcess]:
        """Return monthly review processes matching optional filters."""
        ...

    @abstractmethod
    async def delete_review(self, process_id: MonthlyReviewProcessId) -> None:
        """Delete a monthly review process by ID."""
        ...

    @abstractmethod
    async def start_review(self, process_id: MonthlyReviewProcessId) -> MonthlyReviewProcess:
        """Transition the process from NOT_STARTED to IN_PROGRESS."""
        ...

    @abstractmethod
    async def cancel_review(self, process_id: MonthlyReviewProcessId) -> MonthlyReviewProcess:
        """Cancel the monthly review process."""
        ...

    @abstractmethod
    async def upsert_interview(
            self,
            process_id: MonthlyReviewProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> tuple[Interview, bool]:
        """Create or replace the interview for the given monthly review process."""
        ...

    @abstractmethod
    async def get_interview(self, process_id: MonthlyReviewProcessId) -> Interview:
        """Retrieve the interview associated with the given monthly review process."""
        ...

    @abstractmethod
    async def start_interview(self, process_id: MonthlyReviewProcessId) -> Interview:
        """Transition the process's interview from SCHEDULED to IN_PROGRESS."""
        ...

    @abstractmethod
    async def complete_interview(self, process_id: MonthlyReviewProcessId) -> Interview:
        """Transition the process's interview from IN_PROGRESS to COMPLETED."""
        ...

    @abstractmethod
    async def add_interview_turns(
            self,
            process_id: MonthlyReviewProcessId,
            turns: list[InterviewTurn],
    ) -> Interview:
        """Append turns to the in-progress interview of the given process."""
        ...

    @abstractmethod
    async def generate_dossier(self, process_id: MonthlyReviewProcessId) -> Dossier:
        """Generate and persist the dossier for a process, then complete it.

        Reads the process's completed interview, generates dossier content,
        persists the dossier, advances it to DRAFT, completes the monthly
        review process (IN_PROGRESS -> FINISHED), and publishes the
        corresponding outbound events.
        """
        ...

    @abstractmethod
    async def get_dossier(self, process_id: MonthlyReviewProcessId) -> Dossier:
        """Retrieve the dossier for the given monthly review process."""
        ...
