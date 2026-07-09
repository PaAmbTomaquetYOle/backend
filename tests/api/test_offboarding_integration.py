"""Integration tests — full stack with SQLite in-memory DB.

Writes are Kafka-only (see `domain/events/inbound_events.py` and
`tests/events/handlers`), so test fixtures seed data directly via the
repositories — mirroring what a Kafka handler would persist — instead of
through REST. This module exercises the surviving read-only REST endpoints.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.domain import (
    Dossier,
    DossierId,
    Interview,
    NotGeneratedDossierState,
    OffboardingProcess,
    OffboardingProcessId,
    ScheduledInterviewState,
)
from app.domain.offboarding.id import EmployeeId, InterviewId, ManagerId
from app.domain.offboarding.state.not_started import NotStartedState
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.adapters.repositories.dossier import DossierRepository
from app.infrastructure.adapters.repositories.interview import InterviewRepository
from app.infrastructure.adapters.repositories.offboarding_process import (
    OffboardingProcessRepository,
)
from app.infrastructure.persistence import models as _models  # noqa: F401
from app.infrastructure.persistence.database import get_session
from app.main import create_app


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    yield eng
    SQLModel.metadata.drop_all(eng)


@pytest.fixture
def client(engine) -> TestClient:
    app = create_app()  # triggers model imports → registers SQLModel metadata

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_service] = lambda: {
        "iss": "test-service", "aud": "offboardme-backend"
    }
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Seed helpers — insert directly via repositories, as a Kafka handler would.
# ---------------------------------------------------------------------------

def _seed_process(engine, state=None) -> OffboardingProcess:
    process = OffboardingProcess(
        process_id=OffboardingProcessId(),
        state=state or NotStartedState(),
        employee_id=EmployeeId(str(uuid4())),
        manager_id=ManagerId(str(uuid4())),
        created_at=datetime.now(UTC),
    )
    with Session(engine) as session:
        OffboardingProcessRepository(session).save(process)
    return process


def _seed_interview(engine, process_id: OffboardingProcessId) -> Interview:
    interview = Interview(
        interview_id=InterviewId(),
        process_id=process_id,
        state=ScheduledInterviewState(),
        scheduled_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    with Session(engine) as session:
        InterviewRepository(session).save(interview)
    return interview


def _seed_dossier(engine, process_id: OffboardingProcessId, interview_id: InterviewId) -> Dossier:
    dossier = Dossier(
        dossier_id=DossierId(),
        process_id=process_id,
        interview_id=interview_id,
        state=NotGeneratedDossierState(),
        created_at=datetime.now(UTC),
    )
    with Session(engine) as session:
        DossierRepository(session).save(dossier)
    return dossier


# ---------------------------------------------------------------------------
# Process reads
# ---------------------------------------------------------------------------

class TestProcessReads:
    def test_get_returns_200(self, client: TestClient, engine) -> None:
        process = _seed_process(engine)

        r = client.get(f"/api/v1/offboarding/{process.process_id.get_id()}")

        assert r.status_code == 200
        assert r.json()["id"] == str(process.process_id.get_id())

    def test_get_404_unknown_id(self, client: TestClient) -> None:
        r = client.get(f"/api/v1/offboarding/{uuid4()}")
        assert r.status_code == 404

    def test_list_returns_all(self, client: TestClient, engine) -> None:
        _seed_process(engine)
        _seed_process(engine)

        r = client.get("/api/v1/offboarding")

        assert r.status_code == 200
        assert r.json()["count"] >= 2

    def test_list_filter_by_state(self, client: TestClient, engine) -> None:
        _seed_process(engine)

        r = client.get("/api/v1/offboarding?state=not_started")

        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["state"] == "not_started"


# ---------------------------------------------------------------------------
# Interview reads
# ---------------------------------------------------------------------------

class TestInterviewReads:
    def test_get_interview(self, client: TestClient, engine) -> None:
        process = _seed_process(engine)
        _seed_interview(engine, process.process_id)

        r = client.get(f"/api/v1/offboarding/{process.process_id.get_id()}/interview")

        assert r.status_code == 200
        assert r.json()["process_id"] == str(process.process_id.get_id())

    def test_get_interview_404_when_not_created(self, client: TestClient, engine) -> None:
        process = _seed_process(engine)

        r = client.get(f"/api/v1/offboarding/{process.process_id.get_id()}/interview")

        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Dossier reads
# ---------------------------------------------------------------------------

class TestDossierReads:
    def test_get_dossier_returns_200(self, client: TestClient, engine) -> None:
        process = _seed_process(engine)
        interview = _seed_interview(engine, process.process_id)
        _seed_dossier(engine, process.process_id, interview.interview_id)

        r = client.get(f"/api/v1/offboarding/{process.process_id.get_id()}/dossier")

        assert r.status_code == 200
        assert r.json()["process_id"] == str(process.process_id.get_id())

    def test_get_dossier_404_not_created(self, client: TestClient, engine) -> None:
        process = _seed_process(engine)

        r = client.get(f"/api/v1/offboarding/{process.process_id.get_id()}/dossier")

        assert r.status_code == 404
