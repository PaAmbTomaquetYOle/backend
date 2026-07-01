"""Integration tests — full stack with SQLite in-memory DB."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.infrastructure.persistence import models as _models  # noqa: F401
from app.infrastructure.persistence.database import get_session
from app.main import create_app
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service


@pytest.fixture
def client() -> TestClient:
    app = create_app()  # triggers model imports → registers SQLModel metadata
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)

    def override_session():
        with Session(eng) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_service] = lambda: {"iss": "test-service", "aud": "offboardme-backend"}
    yield TestClient(app, raise_server_exceptions=True)
    SQLModel.metadata.drop_all(eng)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_process(client: TestClient) -> dict:
    r = client.post("/api/v1/offboarding", json={
        "employee_id": str(uuid4()),
        "manager_id": str(uuid4()),
    })
    assert r.status_code == 201
    return r.json()


def _upsert_interview(client: TestClient, process_id: str) -> dict:
    r = client.put(f"/api/v1/offboarding/{process_id}/interview", json={
        "scheduled_at": datetime.now(UTC).isoformat(),
        "turns": [],
    })
    assert r.status_code in (200, 201)
    return r.json()


# ---------------------------------------------------------------------------
# Process CRUD
# ---------------------------------------------------------------------------

class TestProcessCRUD:
    def test_create_returns_201(self, client: TestClient) -> None:
        r = client.post("/api/v1/offboarding", json={
            "employee_id": str(uuid4()),
            "manager_id": str(uuid4()),
        })
        assert r.status_code == 201
        body = r.json()
        assert body["state"] == "not_started"
        assert body["interview_id"] is None
        assert body["dossier_id"] is None

    def test_get_returns_200(self, client: TestClient) -> None:
        process = _create_process(client)

        r = client.get(f"/api/v1/offboarding/{process['id']}")

        assert r.status_code == 200
        assert r.json()["id"] == process["id"]

    def test_get_404_unknown_id(self, client: TestClient) -> None:
        r = client.get(f"/api/v1/offboarding/{uuid4()}")
        assert r.status_code == 404

    def test_list_returns_all(self, client: TestClient) -> None:
        _create_process(client)
        _create_process(client)

        r = client.get("/api/v1/offboarding")

        assert r.status_code == 200
        assert r.json()["count"] >= 2

    def test_list_filter_by_state(self, client: TestClient) -> None:
        _create_process(client)

        r = client.get("/api/v1/offboarding?state=not_started")

        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["state"] == "not_started"

    def test_delete_returns_204(self, client: TestClient) -> None:
        process = _create_process(client)

        r = client.delete(f"/api/v1/offboarding/{process['id']}")

        assert r.status_code == 204

        r2 = client.get(f"/api/v1/offboarding/{process['id']}")
        assert r2.status_code == 404

    def test_delete_404_unknown_id(self, client: TestClient) -> None:
        r = client.delete(f"/api/v1/offboarding/{uuid4()}")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Process state transitions
# ---------------------------------------------------------------------------

class TestProcessTransitions:
    def test_full_happy_path(self, client: TestClient) -> None:
        p = _create_process(client)
        pid = p["id"]

        r = client.patch(f"/api/v1/offboarding/{pid}/start")
        assert r.status_code == 200
        assert r.json()["state"] == "in_progress"

        r = client.patch(f"/api/v1/offboarding/{pid}/submit-for-review")
        assert r.status_code == 200
        assert r.json()["state"] == "pending_revision"

        r = client.patch(f"/api/v1/offboarding/{pid}/complete")
        assert r.status_code == 200
        assert r.json()["state"] == "finished"

    def test_cancel_from_not_started(self, client: TestClient) -> None:
        p = _create_process(client)

        r = client.patch(f"/api/v1/offboarding/{p['id']}/cancel")

        assert r.status_code == 200
        assert r.json()["state"] == "cancelled"

    def test_invalid_transition_returns_409(self, client: TestClient) -> None:
        p = _create_process(client)

        r = client.patch(f"/api/v1/offboarding/{p['id']}/submit-for-review")

        assert r.status_code == 409

    def test_transition_404_unknown_id(self, client: TestClient) -> None:
        r = client.patch(f"/api/v1/offboarding/{uuid4()}/start")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Interview upsert
# ---------------------------------------------------------------------------

class TestInterviewUpsert:
    def test_creates_interview_returns_201(self, client: TestClient) -> None:
        p = _create_process(client)

        r = client.put(f"/api/v1/offboarding/{p['id']}/interview", json={
            "scheduled_at": datetime.now(UTC).isoformat(),
            "turns": [],
        })

        assert r.status_code == 201
        body = r.json()
        assert body["state"] == "scheduled"
        assert body["process_id"] == p["id"]

    def test_upsert_replaces_turns_returns_200(self, client: TestClient) -> None:
        p = _create_process(client)
        _upsert_interview(client, p["id"])

        r = client.put(f"/api/v1/offboarding/{p['id']}/interview", json={
            "scheduled_at": datetime.now(UTC).isoformat(),
            "turns": [],
        })

        assert r.status_code == 200

    def test_get_interview(self, client: TestClient) -> None:
        p = _create_process(client)
        _upsert_interview(client, p["id"])

        r = client.get(f"/api/v1/offboarding/{p['id']}/interview")

        assert r.status_code == 200
        assert r.json()["process_id"] == p["id"]

    def test_get_interview_404_when_not_created(self, client: TestClient) -> None:
        p = _create_process(client)

        r = client.get(f"/api/v1/offboarding/{p['id']}/interview")

        assert r.status_code == 404

    def test_interview_transitions(self, client: TestClient) -> None:
        p = _create_process(client)
        _upsert_interview(client, p["id"])

        r = client.patch(f"/api/v1/offboarding/{p['id']}/interview/start")
        assert r.status_code == 200
        assert r.json()["state"] == "in_progress"

        r = client.patch(f"/api/v1/offboarding/{p['id']}/interview/complete")
        assert r.status_code == 200
        assert r.json()["state"] == "completed"

    def test_interview_404_process_not_found(self, client: TestClient) -> None:
        r = client.put(f"/api/v1/offboarding/{uuid4()}/interview", json={
            "scheduled_at": datetime.now(UTC).isoformat(),
        })
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Dossier
# ---------------------------------------------------------------------------

class TestDossier:
    def test_create_dossier_returns_201(self, client: TestClient) -> None:
        p = _create_process(client)
        _upsert_interview(client, p["id"])

        r = client.post(f"/api/v1/offboarding/{p['id']}/dossier", json={"sections": []})

        assert r.status_code == 201
        body = r.json()
        assert body["process_id"] == p["id"]
        assert body["state"] == "not_generated"

    def test_get_dossier_returns_200(self, client: TestClient) -> None:
        p = _create_process(client)
        _upsert_interview(client, p["id"])
        client.post(f"/api/v1/offboarding/{p['id']}/dossier", json={"sections": []})

        r = client.get(f"/api/v1/offboarding/{p['id']}/dossier")

        assert r.status_code == 200
        assert r.json()["process_id"] == p["id"]

    def test_create_dossier_409_already_exists(self, client: TestClient) -> None:
        p = _create_process(client)
        _upsert_interview(client, p["id"])
        client.post(f"/api/v1/offboarding/{p['id']}/dossier", json={"sections": []})

        r = client.post(f"/api/v1/offboarding/{p['id']}/dossier", json={"sections": []})

        assert r.status_code == 409

    def test_create_dossier_404_no_interview(self, client: TestClient) -> None:
        p = _create_process(client)

        r = client.post(f"/api/v1/offboarding/{p['id']}/dossier", json={"sections": []})

        assert r.status_code == 404

    def test_get_dossier_404_not_created(self, client: TestClient) -> None:
        p = _create_process(client)

        r = client.get(f"/api/v1/offboarding/{p['id']}/dossier")

        assert r.status_code == 404

    def test_full_e2e_flow(self, client: TestClient) -> None:
        """Full E2E: create → start → interview → dossier."""
        p = _create_process(client)
        pid = p["id"]

        client.patch(f"/api/v1/offboarding/{pid}/start")

        r = client.put(f"/api/v1/offboarding/{pid}/interview", json={
            "scheduled_at": datetime.now(UTC).isoformat(),
            "turns": [{
                "turn_type": "question",
                "speaker_role": "interviewer",
                "timestamp": datetime.now(UTC).isoformat(),
                "content": "What are your main responsibilities?",
                "order": 0,
            }],
        })
        assert r.status_code == 201

        r = client.post(f"/api/v1/offboarding/{pid}/dossier", json={
            "summary": "Offboarding summary",
            "sections": [{
                "title": "Responsibilities",
                "section_type": "responsibilities",
                "responsibilities": ["Lead the backend team", "Review PRs"],
            }],
        })
        assert r.status_code == 201
        body = r.json()
        assert body["summary"] == "Offboarding summary"
        assert len(body["sections"]) == 1
        assert body["sections"][0]["section_type"] == "responsibilities"

        r = client.get(f"/api/v1/offboarding/{pid}/dossier")
        assert r.status_code == 200
