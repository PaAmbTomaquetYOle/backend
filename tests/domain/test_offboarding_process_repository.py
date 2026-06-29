"""Unit tests for OffboardingProcessRepository using in-memory SQLite."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.domain.offboarding.id import EmployeeId, ManagerId, OffboardingProcessId
from app.domain.offboarding.process import OffboardingProcess
from app.domain.offboarding.state.in_progress import InProgressState
from app.domain.offboarding.state.not_started import NotStartedState
from app.infrastructure.adapters.repositories.offboarding_process import OffboardingProcessRepository
from app.infrastructure.persistence import models as _models  # noqa: F401 — registers tables


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="repository")
def repository_fixture(session):
    return OffboardingProcessRepository(session)


def make_process(
    state=None,
    employee_id: EmployeeId | None = None,
    manager_id: ManagerId | None = None,
) -> OffboardingProcess:
    return OffboardingProcess(
        process_id=OffboardingProcessId(),
        state=state or NotStartedState(),
        employee_id=employee_id or EmployeeId(),
        manager_id=manager_id or ManagerId(),
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


class TestSave:
    def test_save_and_find_by_id(self, repository):
        process = make_process()
        repository.save(process)

        found = repository.find_by_id(process.process_id)
        assert found is not None
        assert found.process_id.is_equal(process.process_id)

    def test_save_twice_overwrites(self, repository):
        process = make_process()
        repository.save(process)
        process.start()
        repository.save(process)

        found = repository.find_by_id(process.process_id)
        assert found is not None
        from app.domain.enums import OffboardingProcessStateEnum
        assert found.state.get_state() == OffboardingProcessStateEnum.IN_PROGRESS


class TestFindById:
    def test_returns_none_when_not_found(self, repository):
        assert repository.find_by_id(OffboardingProcessId()) is None

    def test_state_round_trip(self, repository):
        process = make_process(state=InProgressState())
        repository.save(process)

        found = repository.find_by_id(process.process_id)
        from app.domain.enums import OffboardingProcessStateEnum
        assert found.state.get_state() == OffboardingProcessStateEnum.IN_PROGRESS


class TestFindByEmployeeId:
    def test_returns_processes_for_employee(self, repository):
        employee = EmployeeId()
        p1 = make_process(employee_id=employee)
        p2 = make_process(employee_id=employee)
        other = make_process()
        repository.save(p1)
        repository.save(p2)
        repository.save(other)

        results = repository.find_by_employee_id(employee)
        ids = {r.process_id.get_id() for r in results}
        assert p1.process_id.get_id() in ids
        assert p2.process_id.get_id() in ids
        assert other.process_id.get_id() not in ids

    def test_returns_empty_for_unknown_employee(self, repository):
        assert repository.find_by_employee_id(EmployeeId()) == []


class TestFindAll:
    def test_empty_returns_empty_list(self, repository):
        assert repository.find_all() == []

    def test_returns_all_saved_processes(self, repository):
        p1 = make_process()
        p2 = make_process()
        repository.save(p1)
        repository.save(p2)

        results = repository.find_all()
        assert len(results) == 2


class TestDelete:
    def test_delete_existing_process(self, repository):
        process = make_process()
        repository.save(process)
        repository.delete(process.process_id)

        assert repository.find_by_id(process.process_id) is None

    def test_delete_nonexistent_is_noop(self, repository):
        repository.delete(OffboardingProcessId())  # must not raise
