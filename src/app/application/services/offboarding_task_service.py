"""Concrete implementation of the offboarding task service."""

from app.application.ports.offboarding_task import IOffboardingTaskRepository
from app.application.service_interfaces.offboarding_task_service_interface import (
    IOffboardingTaskService,
)
from app.domain.offboarding.id import OffboardingProcessId
from app.domain.offboarding.task import OffboardingTask


class OffboardingTaskService(IOffboardingTaskService):
    """Orchestrates offboarding task use cases: replace and list (SA-18).

    A focused service, mirroring SopCandidateService — tasks are a distinct, replaceable
    snapshot per process rather than a mutation folded into OffboardingProcessService.
    """

    def __init__(self, repo: IOffboardingTaskRepository) -> None:
        """Set up the service with a repository.

        Args:
            repo: The repository used to persist and retrieve tasks.
        """
        self._repo = repo

    async def record_extracted_tasks(
        self, process_id: OffboardingProcessId, tasks: list[OffboardingTask]
    ) -> None:
        """Persist the full set of tasks extracted for a process, replacing any prior set."""
        await self._repo.replace_for_process(process_id, tasks)

    async def list_for_process(
        self, process_id: OffboardingProcessId
    ) -> list[OffboardingTask]:
        """Return every task stored for the given process."""
        return await self._repo.find_by_process_id(process_id)
