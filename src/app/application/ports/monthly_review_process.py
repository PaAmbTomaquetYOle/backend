"""Repository port interface for MonthlyReviewProcess."""

from abc import ABC, abstractmethod

from app.domain.monthly_review.id import MonthlyReviewProcessId
from app.domain.monthly_review.process import MonthlyReviewProcess
from app.domain.offboarding.id import EmployeeId


class IMonthlyReviewProcessRepository(ABC):
    """Interface for the monthly review process repository."""

    @abstractmethod
    async def save(self, process: MonthlyReviewProcess) -> None:
        """Persist a process (insert or update by ID)."""

    @abstractmethod
    async def find_by_id(self, process_id: MonthlyReviewProcessId) -> MonthlyReviewProcess | None:
        """Return the process with the given ID, or None if not found."""

    @abstractmethod
    async def find_by_employee_id(self, employee_id: EmployeeId) -> list[MonthlyReviewProcess]:
        """Return all processes for the given employee."""

    @abstractmethod
    async def find_all(self) -> list[MonthlyReviewProcess]:
        """Return all stored processes."""

    @abstractmethod
    async def delete(self, process_id: MonthlyReviewProcessId) -> None:
        """Remove the process with the given ID (no-op if not found)."""
