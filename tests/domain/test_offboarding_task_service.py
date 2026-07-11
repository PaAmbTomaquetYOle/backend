"""Unit tests for OffboardingTaskService using a fake in-memory repository."""

from __future__ import annotations

import pytest

from app.application.services.offboarding_task_service import OffboardingTaskService
from app.domain.enums import TaskSourceEnum
from app.domain.offboarding.id import OffboardingProcessId
from app.domain.offboarding.task import OffboardingTask


class FakeOffboardingTaskRepository:
    def __init__(self):
        self._by_process: dict[str, list[OffboardingTask]] = {}

    async def replace_for_process(self, process_id, tasks):
        self._by_process[process_id.get_id()] = list(tasks)

    async def find_by_process_id(self, process_id):
        return self._by_process.get(process_id.get_id(), [])


@pytest.fixture(name="repo")
def repo_fixture():
    return FakeOffboardingTaskRepository()


@pytest.fixture(name="service")
def service_fixture(repo):
    return OffboardingTaskService(repo)


def make_task(process_id: OffboardingProcessId, task_id: str = "PROJ-1") -> OffboardingTask:
    return OffboardingTask(
        process_id=process_id,
        task_id=task_id,
        title="Fix the thing",
        source=TaskSourceEnum.JIRA,
        status="in_progress",
    )


@pytest.mark.anyio
class TestRecordExtractedTasks:
    async def test_persists_the_given_tasks(self, service):
        process_id = OffboardingProcessId()
        await service.record_extracted_tasks(process_id, [make_task(process_id)])

        tasks = await service.list_for_process(process_id)
        assert len(tasks) == 1
        assert tasks[0].task_id == "PROJ-1"

    async def test_replaces_the_prior_set(self, service):
        process_id = OffboardingProcessId()
        await service.record_extracted_tasks(process_id, [make_task(process_id, "PROJ-1")])
        await service.record_extracted_tasks(process_id, [make_task(process_id, "PROJ-2")])

        tasks = await service.list_for_process(process_id)
        assert {t.task_id for t in tasks} == {"PROJ-2"}


@pytest.mark.anyio
class TestListForProcess:
    async def test_returns_empty_list_when_none_recorded(self, service):
        assert await service.list_for_process(OffboardingProcessId()) == []
