"""Repository port interface for OffboardingTask."""

from abc import ABC, abstractmethod

from app.domain.offboarding.id import OffboardingProcessId
from app.domain.offboarding.task import OffboardingTask


class IOffboardingTaskRepository(ABC):
    """Interface for the offboarding task repository."""

    @abstractmethod
    async def replace_for_process(
        self, process_id: OffboardingProcessId, tasks: list[OffboardingTask]
    ) -> None:
        """Replace the full set of tasks stored for a process with the given tasks.

        Tasks are extracted once per interview (SA-18) and re-extraction always carries the
        current full set, so persistence is a full-set replace rather than an incremental merge.
        """

    @abstractmethod
    async def find_by_process_id(
        self, process_id: OffboardingProcessId
    ) -> list[OffboardingTask]:
        """Return every task stored for the given process."""
