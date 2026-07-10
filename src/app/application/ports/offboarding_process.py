"""Repository port interface for OffboardingProcess."""

from abc import ABC, abstractmethod

from app.domain.offboarding.id import EmployeeId, OffboardingProcessId
from app.domain.offboarding.process import OffboardingProcess


class IOffboardingProcessRepository(ABC):
    """Interface for the offboarding process repository."""

    @abstractmethod
    def save(self, process: OffboardingProcess) -> None:
        """Persist a process (insert or update by ID)."""

    @abstractmethod
    def find_by_id(self, process_id: OffboardingProcessId) -> OffboardingProcess | None:
        """Return the process with the given ID, or None if not found."""

    @abstractmethod
    def find_by_employee_id(self, employee_id: EmployeeId) -> list[OffboardingProcess]:
        """Return all processes for the given employee."""

    @abstractmethod
    def find_all(self) -> list[OffboardingProcess]:
        """Return all stored processes."""

    @abstractmethod
    def delete(self, process_id: OffboardingProcessId) -> None:
        """Remove the process with the given ID (no-op if not found)."""
