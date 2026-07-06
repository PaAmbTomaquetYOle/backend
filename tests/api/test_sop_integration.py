"""Integration tests for SOP endpoints — full stack with SQLite in-memory DB."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.persistence import models as _models  # noqa: F401
from app.infrastructure.persistence.database import get_session
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
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
    app.dependency_overrides[get_current_service] = lambda: {
        "iss": "test-service", "aud": "offboardme-backend"
    }
    yield TestClient(app, raise_server_exceptions=True)
    SQLModel.metadata.drop_all(eng)


def _create_sop(client: TestClient, content: str = "How to rotate secrets", tags=None) -> dict:
    r = client.post("/api/v1/sops", json={
        "content": content,
        "author": "U1",
        "origin_channel": "C1",
        "tags": tags or ["security"],
    })
    assert r.status_code == 201
    return r.json()


class TestSopCRUD:
    def test_create_returns_201(self, client: TestClient) -> None:
        r = client.post("/api/v1/sops", json={
            "content": "How to rotate secrets",
            "author": "U1",
            "origin_channel": "C1",
            "tags": ["security"],
        })
        assert r.status_code == 201
        body = r.json()
        assert body["version"] == 1
        assert body["tags"] == ["security"]

    def test_get_returns_200(self, client: TestClient) -> None:
        sop = _create_sop(client)

        r = client.get(f"/api/v1/sops/{sop['id']}")

        assert r.status_code == 200
        assert r.json()["id"] == sop["id"]

    def test_get_404_unknown_id(self, client: TestClient) -> None:
        r = client.get(f"/api/v1/sops/{uuid4()}")
        assert r.status_code == 404

    def test_patch_bumps_version(self, client: TestClient) -> None:
        sop = _create_sop(client)

        r = client.patch(f"/api/v1/sops/{sop['id']}", json={"content": "updated content"})

        assert r.status_code == 200
        body = r.json()
        assert body["content"] == "updated content"
        assert body["version"] == 2

    def test_patch_404_unknown_id(self, client: TestClient) -> None:
        r = client.patch(f"/api/v1/sops/{uuid4()}", json={"content": "x"})
        assert r.status_code == 404

    def test_delete_returns_204_and_soft_deletes(self, client: TestClient) -> None:
        sop = _create_sop(client)

        r = client.delete(f"/api/v1/sops/{sop['id']}")
        assert r.status_code == 204

        r2 = client.get(f"/api/v1/sops/{sop['id']}")
        assert r2.status_code == 404

    def test_delete_404_unknown_id(self, client: TestClient) -> None:
        r = client.delete(f"/api/v1/sops/{uuid4()}")
        assert r.status_code == 404


class TestSopSearch:
    def test_search_all_paginated(self, client: TestClient) -> None:
        for i in range(3):
            _create_sop(client, content=f"doc {i}")

        r = client.get("/api/v1/sops?page=1&size=2")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
        assert body["total_pages"] == 2

    def test_search_by_text(self, client: TestClient) -> None:
        _create_sop(client, content="How to rotate secrets")
        _create_sop(client, content="How to onboard a new hire")

        r = client.get("/api/v1/sops?q=rotate")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert "rotate" in body["items"][0]["content"].lower()

    def test_search_by_tags_match_all(self, client: TestClient) -> None:
        _create_sop(client, content="a", tags=["security", "urgent"])
        _create_sop(client, content="b", tags=["security"])

        r = client.get("/api/v1/sops?tags=security&tags=urgent")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["items"][0]["content"] == "a"

    def test_deleted_sops_excluded_from_search(self, client: TestClient) -> None:
        sop = _create_sop(client)
        client.delete(f"/api/v1/sops/{sop['id']}")

        r = client.get("/api/v1/sops")

        assert r.status_code == 200
        assert sop["id"] not in [i["id"] for i in r.json()["items"]]
