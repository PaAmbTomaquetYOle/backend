"""Repository port interface for AnnualReviewProcess."""

from abc import ABC, abstractmethod

from app.domain.annual_review.id import AnnualReviewProcessId
from app.domain.annual_review.process import AnnualReviewProcess
from app.domain.offboarding.id import EmployeeId


class IAnnualReviewProcessRepository(ABC):
    """Interface for the annual review process repository."""

    @abstractmethod
    async def save(self, process: AnnualReviewProcess) -> None:
        """Persist a process (insert or update by ID)."""

    @abstractmethod
    async def find_by_id(self, process_id: AnnualReviewProcessId) -> AnnualReviewProcess | None:
        """Return the process with the given ID, or None if not found."""

    @abstractmethod
    async def find_by_employee_id(self, employee_id: EmployeeId) -> list[AnnualReviewProcess]:
        """Return all processes for the given employee."""

    @abstractmethod
    async def find_all(self) -> list[AnnualReviewProcess]:
        """Return all stored processes."""

    @abstractmethod
    async def delete(self, process_id: AnnualReviewProcessId) -> None:
        """Remove the process with the given ID (no-op if not found)."""
