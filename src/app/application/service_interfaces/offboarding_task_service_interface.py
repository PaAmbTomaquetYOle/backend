"""Inbound port (service contract) for offboarding task use cases."""

from abc import ABC, abstractmethod

from app.domain.offboarding.id import OffboardingProcessId
from app.domain.offboarding.task import OffboardingTask


class IOffboardingTaskService(ABC):
    """Use cases for persisting and retrieving a departing employee's extracted tasks (SA-18)."""

    @abstractmethod
    async def record_extracted_tasks(
        self, process_id: OffboardingProcessId, tasks: list[OffboardingTask]
    ) -> None:
        """Persist the full set of tasks extracted for a process, replacing any prior set."""

    @abstractmethod
    async def list_for_process(
        self, process_id: OffboardingProcessId
    ) -> list[OffboardingTask]:
        """Return every task stored for the given process, for the read model and rehydration."""
