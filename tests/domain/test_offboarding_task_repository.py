"""Unit tests for OffboardingTaskRepository using in-memory async SQLite."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from app.domain.enums import TaskSourceEnum
from app.domain.offboarding.id import OffboardingProcessId
from app.domain.offboarding.task import OffboardingTask
from app.infrastructure.adapters.repositories.offboarding_task import OffboardingTaskRepository
from app.infrastructure.persistence import models as _models  # noqa: F401 — registers tables


@pytest.fixture(name="engine")
async def engine_fixture():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(name="session")
async def session_fixture(engine):
    async with AsyncSession(engine) as session:
        yield session


@pytest.fixture(name="repository")
def repository_fixture(session):
    return OffboardingTaskRepository(session)


def make_task(
    process_id: OffboardingProcessId,
    task_id: str = "PROJ-1",
    source: TaskSourceEnum = TaskSourceEnum.JIRA,
) -> OffboardingTask:
    return OffboardingTask(
        process_id=process_id,
        task_id=task_id,
        title="Fix the thing",
        source=source,
        status="in_progress",
        url="https://jira/PROJ-1",
        description="desc",
    )


@pytest.mark.anyio
class TestReplaceForProcess:
    async def test_replace_persists_tasks_for_process(self, repository):
        process_id = OffboardingProcessId()
        await repository.replace_for_process(process_id, [make_task(process_id)])

        found = await repository.find_by_process_id(process_id)
        assert len(found) == 1
        assert found[0].task_id == "PROJ-1"
        assert found[0].source == TaskSourceEnum.JIRA

    async def test_replace_removes_the_prior_set(self, repository):
        process_id = OffboardingProcessId()
        await repository.replace_for_process(process_id, [make_task(process_id, "PROJ-1")])
        await repository.replace_for_process(process_id, [make_task(process_id, "PROJ-2")])

        found = await repository.find_by_process_id(process_id)
        assert {t.task_id for t in found} == {"PROJ-2"}

    async def test_replace_with_empty_list_clears_tasks(self, repository):
        process_id = OffboardingProcessId()
        await repository.replace_for_process(process_id, [make_task(process_id)])
        await repository.replace_for_process(process_id, [])

        assert await repository.find_by_process_id(process_id) == []

    async def test_does_not_affect_other_processes(self, repository):
        process_a = OffboardingProcessId()
        process_b = OffboardingProcessId()
        await repository.replace_for_process(process_a, [make_task(process_a, "PROJ-A")])
        await repository.replace_for_process(process_b, [make_task(process_b, "PROJ-B")])

        found_a = await repository.find_by_process_id(process_a)
        assert {t.task_id for t in found_a} == {"PROJ-A"}


@pytest.mark.anyio
class TestFindByProcessId:
    async def test_returns_empty_list_when_none_stored(self, repository):
        assert await repository.find_by_process_id(OffboardingProcessId()) == []
