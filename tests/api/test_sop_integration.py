"""Integration tests for SOP endpoints — full stack with SQLite in-memory DB.

SOP creation is Kafka-only (``sop.creation_requested``), so test data is
seeded directly via ``SopRepository`` — mirroring what the Kafka handler
would persist — instead of through REST. This module exercises the
surviving REST endpoints (search, get, update, delete).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.domain.sops.sop import Sop
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.adapters.repositories.sop import SopRepository
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
    app = create_app()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_service] = lambda: {
        "iss": "test-service", "aud": "offboardme-backend"
    }
    return TestClient(app, raise_server_exceptions=True)


def _seed_sop(engine, content: str = "How to rotate secrets", tags=None) -> Sop:
    sop = Sop(
        sop_id=SopId(),
        content=content,
        author=AuthorId("U1"),
        tags=tags or ["security"],
        origin_channel=ChannelId("C1"),
        created_at=datetime.now(UTC),
    )
    with Session(engine) as session:
        SopRepository(session).save(sop)
    return sop


class TestSopCRUD:
    def test_get_returns_200(self, client: TestClient, engine) -> None:
        sop = _seed_sop(engine)

        r = client.get(f"/api/v1/sops/{sop.sop_id.get_id()}")

        assert r.status_code == 200
        assert r.json()["id"] == str(sop.sop_id.get_id())

    def test_get_404_unknown_id(self, client: TestClient) -> None:
        r = client.get(f"/api/v1/sops/{uuid4()}")
        assert r.status_code == 404

    def test_patch_bumps_version(self, client: TestClient, engine) -> None:
        sop = _seed_sop(engine)

        r = client.patch(f"/api/v1/sops/{sop.sop_id.get_id()}", json={"content": "updated content"})

        assert r.status_code == 200
        body = r.json()
        assert body["content"] == "updated content"
        assert body["version"] == 2

    def test_patch_404_unknown_id(self, client: TestClient) -> None:
        r = client.patch(f"/api/v1/sops/{uuid4()}", json={"content": "x"})
        assert r.status_code == 404

    def test_delete_returns_204_and_soft_deletes(self, client: TestClient, engine) -> None:
        sop = _seed_sop(engine)

        r = client.delete(f"/api/v1/sops/{sop.sop_id.get_id()}")
        assert r.status_code == 204

        r2 = client.get(f"/api/v1/sops/{sop.sop_id.get_id()}")
        assert r2.status_code == 404

    def test_delete_404_unknown_id(self, client: TestClient) -> None:
        r = client.delete(f"/api/v1/sops/{uuid4()}")
        assert r.status_code == 404


class TestSopSearch:
    def test_search_all_paginated(self, client: TestClient, engine) -> None:
        for i in range(3):
            _seed_sop(engine, content=f"doc {i}")

        r = client.get("/api/v1/sops?page=1&size=2")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
        assert body["total_pages"] == 2

    def test_search_by_text(self, client: TestClient, engine) -> None:
        _seed_sop(engine, content="How to rotate secrets")
        _seed_sop(engine, content="How to onboard a new hire")

        r = client.get("/api/v1/sops?q=rotate")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert "rotate" in body["items"][0]["content"].lower()

    def test_search_by_tags_match_all(self, client: TestClient, engine) -> None:
        _seed_sop(engine, content="a", tags=["security", "urgent"])
        _seed_sop(engine, content="b", tags=["security"])

        r = client.get("/api/v1/sops?tags=security&tags=urgent")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["items"][0]["content"] == "a"

    def test_deleted_sops_excluded_from_search(self, client: TestClient, engine) -> None:
        sop = _seed_sop(engine)
        client.delete(f"/api/v1/sops/{sop.sop_id.get_id()}")

        r = client.get("/api/v1/sops")

        assert r.status_code == 200
        assert str(sop.sop_id.get_id()) not in [i["id"] for i in r.json()["items"]]
