"""Integration tests — full stack with async in-memory SQLite DB.

Writes are Kafka-only (see `domain/events/inbound_events.py` and
`tests/events/handlers`), so test fixtures seed data directly via the
repositories — mirroring what a Kafka handler would persist — instead of
through REST. This module exercises the surviving read-only REST endpoints.
"""

from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from app.domain import (
    Dossier,
    DossierId,
    Interview,
    NotGeneratedDossierState,
    OffboardingProcess,
    OffboardingProcessId,
    ScheduledInterviewState,
)
from app.domain.enums import TaskSourceEnum
from app.domain.offboarding.id import EmployeeId, InterviewId, ManagerId
from app.domain.offboarding.state.not_started import NotStartedState
from app.domain.offboarding.task import OffboardingTask
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.adapters.repositories.dossier import DossierRepository
from app.infrastructure.adapters.repositories.interview import InterviewRepository
from app.infrastructure.adapters.repositories.offboarding_process import (
    OffboardingProcessRepository,
)
from app.infrastructure.adapters.repositories.offboarding_task import OffboardingTaskRepository
from app.infrastructure.persistence import models as _models  # noqa: F401
from app.infrastructure.persistence.database import get_session
from app.main import create_app

pytestmark = pytest.mark.anyio


@pytest.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite://")
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await eng.dispose()


@pytest.fixture
async def client(engine):
    app = create_app()  # triggers model imports → registers SQLModel metadata

    async def override_session():
        async with AsyncSession(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_service] = lambda: {
        "iss": "test-service", "aud": "offboardme-backend"
    }
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Seed helpers — insert directly via repositories, as a Kafka handler would.
# ---------------------------------------------------------------------------

async def _seed_process(engine, state=None) -> OffboardingProcess:
    process = OffboardingProcess(
        process_id=OffboardingProcessId(),
        state=state or NotStartedState(),
        employee_id=EmployeeId(str(uuid4())),
        manager_id=ManagerId(str(uuid4())),
        created_at=datetime.now(UTC),
    )
    async with AsyncSession(engine) as session:
        await OffboardingProcessRepository(session).save(process)
    return process


async def _seed_interview(engine, process_id: OffboardingProcessId) -> Interview:
    interview = Interview(
        interview_id=InterviewId(),
        process_id=process_id,
        state=ScheduledInterviewState(),
        scheduled_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    async with AsyncSession(engine) as session:
        await InterviewRepository(session).save(interview)
    return interview


async def _seed_dossier(
    engine, process_id: OffboardingProcessId, interview_id: InterviewId
) -> Dossier:
    dossier = Dossier(
        dossier_id=DossierId(),
        process_id=process_id,
        interview_id=interview_id,
        state=NotGeneratedDossierState(),
        created_at=datetime.now(UTC),
    )
    async with AsyncSession(engine) as session:
        await DossierRepository(session).save(dossier)
    return dossier


# ---------------------------------------------------------------------------
# Process reads
# ---------------------------------------------------------------------------

class TestProcessReads:
    async def test_get_returns_200(self, client: httpx.AsyncClient, engine) -> None:
        process = await _seed_process(engine)

        r = await client.get(f"/api/v1/offboarding/{process.process_id.get_id()}")

        assert r.status_code == 200
        assert r.json()["id"] == str(process.process_id.get_id())

    async def test_get_404_unknown_id(self, client: httpx.AsyncClient) -> None:
        r = await client.get(f"/api/v1/offboarding/{uuid4()}")
        assert r.status_code == 404

    async def test_list_returns_all(self, client: httpx.AsyncClient, engine) -> None:
        await _seed_process(engine)
        await _seed_process(engine)

        r = await client.get("/api/v1/offboarding")

        assert r.status_code == 200
        assert r.json()["count"] >= 2

    async def test_list_filter_by_state(self, client: httpx.AsyncClient, engine) -> None:
        await _seed_process(engine)

        r = await client.get("/api/v1/offboarding?state=not_started")

        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["state"] == "not_started"


async def _seed_tasks(
    engine, process_id: OffboardingProcessId, tasks: list[OffboardingTask]
) -> None:
    async with AsyncSession(engine) as session:
        await OffboardingTaskRepository(session).replace_for_process(process_id, tasks)


# ---------------------------------------------------------------------------
# Interview reads
# ---------------------------------------------------------------------------

class TestInterviewReads:
    async def test_get_interview(self, client: httpx.AsyncClient, engine) -> None:
        process = await _seed_process(engine)
        await _seed_interview(engine, process.process_id)

        r = await client.get(f"/api/v1/offboarding/{process.process_id.get_id()}/interview")

        assert r.status_code == 200
        assert r.json()["process_id"] == str(process.process_id.get_id())

    async def test_get_interview_404_when_not_created(
        self, client: httpx.AsyncClient, engine
    ) -> None:
        process = await _seed_process(engine)

        r = await client.get(f"/api/v1/offboarding/{process.process_id.get_id()}/interview")

        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Dossier reads
# ---------------------------------------------------------------------------

class TestDossierReads:
    async def test_get_dossier_returns_200(self, client: httpx.AsyncClient, engine) -> None:
        process = await _seed_process(engine)
        interview = await _seed_interview(engine, process.process_id)
        await _seed_dossier(engine, process.process_id, interview.interview_id)

        r = await client.get(f"/api/v1/offboarding/{process.process_id.get_id()}/dossier")

        assert r.status_code == 200
        assert r.json()["process_id"] == str(process.process_id.get_id())

    async def test_get_dossier_404_not_created(self, client: httpx.AsyncClient, engine) -> None:
        process = await _seed_process(engine)

        r = await client.get(f"/api/v1/offboarding/{process.process_id.get_id()}/dossier")

        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Task reads (SA-18)
# ---------------------------------------------------------------------------

class TestTaskReads:
    async def test_get_tasks_returns_extracted_tasks(
        self, client: httpx.AsyncClient, engine
    ) -> None:
        process = await _seed_process(engine)
        await _seed_tasks(engine, process.process_id, [
            OffboardingTask(
                process_id=process.process_id,
                task_id="PROJ-1",
                title="Fix the thing",
                source=TaskSourceEnum.JIRA,
                status="in_progress",
                url="https://jira/PROJ-1",
                description="desc",
            ),
        ])

        r = await client.get(f"/api/v1/offboarding/{process.process_id.get_id()}/tasks")

        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == "PROJ-1"
        assert items[0]["source"] == "jira"

    async def test_get_tasks_returns_empty_list_when_none_extracted(
        self, client: httpx.AsyncClient, engine
    ) -> None:
        process = await _seed_process(engine)

        r = await client.get(f"/api/v1/offboarding/{process.process_id.get_id()}/tasks")

        assert r.status_code == 200
        assert r.json()["items"] == []
