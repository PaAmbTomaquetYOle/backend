"""Unit tests for offboarding API endpoints — mock facade, test HTTP layer only.

Writes (create, delete, lifecycle transitions, interview/dossier writes) are
Kafka-only — see ``domain/events/inbound_events.py`` and the corresponding
handler tests under ``tests/events/handlers``. This module only covers the
surviving read-only REST endpoints.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.offboarding_facade_service import OffboardingFacadeService
from app.domain import (
    Interview,
    OffboardingProcess,
    OffboardingProcessId,
    ScheduledInterviewState,
)
from app.domain.exceptions.interview import InterviewNotFoundError
from app.domain.exceptions.offboarding import ProcessNotFoundError
from app.domain.offboarding.id import EmployeeId, InterviewId, ManagerId
from app.domain.offboarding.state.not_started import NotStartedState
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.api.dependencies import (
    offboarding_dossier_facade_dependency,
    offboarding_interview_facade_dependency,
    offboarding_process_facade_dependency,
)
from app.main import create_app


def _make_process(
    process_id: UUID | None = None,
    state=None,
    interview_id: UUID | None = None,
) -> OffboardingProcess:
    pid = process_id or uuid4()
    return OffboardingProcess(
        process_id=OffboardingProcessId(pid),
        state=state or NotStartedState(),
        employee_id=EmployeeId(str(uuid4())),
        manager_id=ManagerId(str(uuid4())),
        created_at=datetime.now(UTC),
        interview_id=InterviewId(interview_id) if interview_id else None,
    )


def _make_interview(process_id: UUID | None = None) -> Interview:
    return Interview(
        interview_id=InterviewId(uuid4()),
        process_id=OffboardingProcessId(process_id or uuid4()),
        state=ScheduledInterviewState(),
        scheduled_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_facade() -> AsyncMock:
    return AsyncMock(spec=OffboardingFacadeService)


@pytest.fixture
def client(mock_facade: AsyncMock) -> TestClient:
    app = create_app()
    app.dependency_overrides[offboarding_process_facade_dependency] = lambda: mock_facade
    app.dependency_overrides[offboarding_interview_facade_dependency] = lambda: mock_facade
    app.dependency_overrides[offboarding_dossier_facade_dependency] = lambda: mock_facade
    app.dependency_overrides[get_current_service] = lambda: {
        "iss": "test-service", "aud": "offboardme-backend"
    }
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /offboarding
# ---------------------------------------------------------------------------

class TestListOffboardings:
    def test_200_returns_list(self, client: TestClient, mock_facade: AsyncMock) -> None:
        processes = [_make_process(), _make_process()]
        mock_facade.list_offboardings.return_value = processes

        r = client.get("/api/v1/offboarding")

        assert r.status_code == 200
        body = r.json()
        assert body["count"] == 2
        assert len(body["items"]) == 2

    def test_200_empty_list(self, client: TestClient, mock_facade: AsyncMock) -> None:
        mock_facade.list_offboardings.return_value = []

        r = client.get("/api/v1/offboarding")

        assert r.status_code == 200
        assert r.json()["count"] == 0

    def test_200_with_state_filter(self, client: TestClient, mock_facade: AsyncMock) -> None:
        mock_facade.list_offboardings.return_value = []

        r = client.get("/api/v1/offboarding?state=not_started")

        assert r.status_code == 200

    def test_422_invalid_state_filter(self, client: TestClient, mock_facade: AsyncMock) -> None:
        r = client.get("/api/v1/offboarding?state=bad_state_value")

        assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /offboarding/{id}
# ---------------------------------------------------------------------------

class TestGetOffboarding:
    def test_200_returns_process(self, client: TestClient, mock_facade: AsyncMock) -> None:
        process = _make_process()
        mock_facade.get_offboarding.return_value = process

        r = client.get(f"/api/v1/offboarding/{process.process_id.get_id()}")

        assert r.status_code == 200
        assert r.json()["id"] == str(process.process_id.get_id())

    def test_404_not_found(self, client: TestClient, mock_facade: AsyncMock) -> None:
        pid = uuid4()
        mock_facade.get_offboarding.side_effect = ProcessNotFoundError(str(pid))

        r = client.get(f"/api/v1/offboarding/{pid}")

        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_422_invalid_uuid(self, client: TestClient) -> None:
        r = client.get("/api/v1/offboarding/not-a-uuid")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /offboarding/{id}/interview
# ---------------------------------------------------------------------------

class TestGetInterview:
    def test_200_returns_interview(self, client: TestClient, mock_facade: AsyncMock) -> None:
        interview = _make_interview()
        mock_facade.get_interview.return_value = interview

        r = client.get(f"/api/v1/offboarding/{uuid4()}/interview")

        assert r.status_code == 200
        assert "id" in r.json()

    def test_404_not_found(self, client: TestClient, mock_facade: AsyncMock) -> None:
        mock_facade.get_interview.side_effect = InterviewNotFoundError()

        r = client.get(f"/api/v1/offboarding/{uuid4()}/interview")

        assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /offboarding/{id}/dossier
# ---------------------------------------------------------------------------

class TestGetDossier:
    def test_200_returns_dossier(self, client: TestClient, mock_facade: AsyncMock) -> None:
        from app.domain import Dossier, DossierId, InterviewId
        from app.domain.dossier.state.not_generated import NotGeneratedDossierState
        process_id = uuid4()
        dossier = Dossier(
            dossier_id=DossierId(uuid4()),
            process_id=OffboardingProcessId(process_id),
            interview_id=InterviewId(uuid4()),
            state=NotGeneratedDossierState(),
            created_at=datetime.now(UTC),
        )
        mock_facade.get_dossier.return_value = dossier

        r = client.get(f"/api/v1/offboarding/{process_id}/dossier")

        assert r.status_code == 200

    def test_404_not_found(self, client: TestClient, mock_facade: AsyncMock) -> None:
        from app.domain.exceptions.dossier import DossierNotFoundError
        mock_facade.get_dossier.side_effect = DossierNotFoundError()

        r = client.get(f"/api/v1/offboarding/{uuid4()}/dossier")

        assert r.status_code == 404
