"""Unit tests for MonthlyReviewProcessRepository using in-memory async SQLite."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from app.domain.enums import MonthlyReviewProcessStateEnum
from app.domain.monthly_review.id import MonthlyReviewProcessId
from app.domain.monthly_review.process import MonthlyReviewProcess
from app.domain.monthly_review.state.in_progress import InProgressState
from app.domain.monthly_review.state.not_started import NotStartedState
from app.domain.offboarding.id import EmployeeId, ManagerId
from app.infrastructure.adapters.repositories.monthly_review_process import (
    MonthlyReviewProcessRepository,
)
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
    return MonthlyReviewProcessRepository(session)


def make_process(
    state=None,
    employee_id: EmployeeId | None = None,
    manager_id: ManagerId | None = None,
) -> MonthlyReviewProcess:
    return MonthlyReviewProcess(
        process_id=MonthlyReviewProcessId(),
        state=state or NotStartedState(),
        employee_id=employee_id or EmployeeId(),
        manager_id=manager_id or ManagerId(),
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.mark.anyio
class TestSave:
    async def test_save_and_find_by_id(self, repository):
        process = make_process()
        await repository.save(process)

        found = await repository.find_by_id(process.process_id)
        assert found is not None
        assert found.process_id.is_equal(process.process_id)

    async def test_save_twice_overwrites(self, repository):
        process = make_process()
        await repository.save(process)
        process.start()
        await repository.save(process)

        found = await repository.find_by_id(process.process_id)
        assert found is not None
        assert found.state.get_state() == MonthlyReviewProcessStateEnum.IN_PROGRESS


@pytest.mark.anyio
class TestFindById:
    async def test_returns_none_when_not_found(self, repository):
        assert await repository.find_by_id(MonthlyReviewProcessId()) is None

    async def test_state_round_trip(self, repository):
        process = make_process(state=InProgressState())
        await repository.save(process)

        found = await repository.find_by_id(process.process_id)
        assert found.state.get_state() == MonthlyReviewProcessStateEnum.IN_PROGRESS


@pytest.mark.anyio
class TestFindByEmployeeId:
    async def test_returns_processes_for_employee(self, repository):
        employee = EmployeeId()
        p1 = make_process(employee_id=employee)
        p2 = make_process(employee_id=employee)
        other = make_process()
        await repository.save(p1)
        await repository.save(p2)
        await repository.save(other)

        results = await repository.find_by_employee_id(employee)
        ids = {r.process_id.get_id() for r in results}
        assert p1.process_id.get_id() in ids
        assert p2.process_id.get_id() in ids
        assert other.process_id.get_id() not in ids

    async def test_returns_empty_for_unknown_employee(self, repository):
        assert await repository.find_by_employee_id(EmployeeId()) == []


@pytest.mark.anyio
class TestFindAll:
    async def test_empty_returns_empty_list(self, repository):
        assert await repository.find_all() == []

    async def test_returns_all_saved_processes(self, repository):
        p1 = make_process()
        p2 = make_process()
        await repository.save(p1)
        await repository.save(p2)

        results = await repository.find_all()
        assert len(results) == 2


@pytest.mark.anyio
class TestDelete:
    async def test_delete_existing_process(self, repository):
        process = make_process()
        await repository.save(process)
        await repository.delete(process.process_id)

        assert await repository.find_by_id(process.process_id) is None

    async def test_delete_nonexistent_is_noop(self, repository):
        await repository.delete(MonthlyReviewProcessId())  # must not raise
