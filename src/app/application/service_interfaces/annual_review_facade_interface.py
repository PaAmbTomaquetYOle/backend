"""Facade service interface for annual review operations. Used by inbound Kafka handlers."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain import (
    AnnualReviewProcess,
    AnnualReviewProcessId,
    AnnualReviewProcessStateEnum,
    Dossier,
    EmployeeId,
    Interview,
    InterviewTurn,
    ManagerId,
)


class IAnnualReviewServiceFacade(ABC):
    """Composed facade for annual review process, interview, and dossier operations.

    Mirrors IOffboardingServiceFacade: AnnualReviewProcess has the same state
    machine as OffboardingProcess (adds PENDING_REVISION), so interview
    completion submits the process for review before dossier generation
    completes it.
    """

    @abstractmethod
    async def create_review(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            employee_name: str | None = None,
            manager_name: str | None = None,
    ) -> AnnualReviewProcess:
        """Create a new annual review process in NOT_STARTED state."""
        ...

    @abstractmethod
    async def get_review(self, process_id: AnnualReviewProcessId) -> AnnualReviewProcess:
        """Retrieve an annual review process by ID."""
        ...

    @abstractmethod
    async def list_reviews(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            state: AnnualReviewProcessStateEnum | None = None,
    ) -> list[AnnualReviewProcess]:
        """Return annual review processes matching optional filters."""
        ...

    @abstractmethod
    async def delete_review(self, process_id: AnnualReviewProcessId) -> None:
        """Delete an annual review process by ID."""
        ...

    @abstractmethod
    async def start_review(self, process_id: AnnualReviewProcessId) -> AnnualReviewProcess:
        """Transition the process from NOT_STARTED to IN_PROGRESS."""
        ...

    @abstractmethod
    async def submit_review_for_review(
            self, process_id: AnnualReviewProcessId
    ) -> AnnualReviewProcess:
        """Transition the process from IN_PROGRESS to PENDING_REVISION."""
        ...

    @abstractmethod
    async def cancel_review(self, process_id: AnnualReviewProcessId) -> AnnualReviewProcess:
        """Cancel the annual review process."""
        ...

    @abstractmethod
    async def upsert_interview(
            self,
            process_id: AnnualReviewProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> tuple[Interview, bool]:
        """Create or replace the interview for the given annual review process."""
        ...

    @abstractmethod
    async def get_interview(self, process_id: AnnualReviewProcessId) -> Interview:
        """Retrieve the interview associated with the given annual review process."""
        ...

    @abstractmethod
    async def start_interview(self, process_id: AnnualReviewProcessId) -> Interview:
        """Transition the process's interview from SCHEDULED to IN_PROGRESS."""
        ...

    @abstractmethod
    async def complete_interview(self, process_id: AnnualReviewProcessId) -> Interview:
        """Transition the process's interview from IN_PROGRESS to COMPLETED."""
        ...

    @abstractmethod
    async def add_interview_turns(
            self,
            process_id: AnnualReviewProcessId,
            turns: list[InterviewTurn],
    ) -> Interview:
        """Append turns to the in-progress interview of the given process."""
        ...

    @abstractmethod
    async def generate_dossier(self, process_id: AnnualReviewProcessId) -> Dossier:
        """Generate and persist the dossier for a process, then complete it.

        Reads the process's completed interview, generates dossier content,
        persists the dossier, advances it to DRAFT, completes the annual
        review process (PENDING_REVISION -> FINISHED), and publishes the
        corresponding outbound events.
        """
        ...

    @abstractmethod
    async def get_dossier(self, process_id: AnnualReviewProcessId) -> Dossier:
        """Retrieve the dossier for the given annual review process."""
        ...
