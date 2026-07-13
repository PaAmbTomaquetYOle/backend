"""Unit tests for SOP API endpoints — mock service, test HTTP layer only.

The full SOP write lifecycle (create/update/delete) is Kafka-only (BE-21) —
see ``tests/events/handlers/`` for the handler tests. This module only
covers the surviving read-only REST endpoints (search, get).
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.read_models.sop_search_hit import SopSearchHit
from app.application.services.sop_service import SopService
from app.domain.exceptions.sops import SopNotFoundError
from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.domain.sops.sop import Sop
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.api.dependencies import sop_service_dependency
from app.main import create_app


def _make_sop(content: str = "How to rotate secrets", tags: list[str] | None = None) -> Sop:
    return Sop(
        sop_id=SopId(),
        title="Rotating secrets",
        content=content,
        author=AuthorId("U1"),
        tags=tags or ["security"],
        origin_channel=ChannelId("C1"),
        created_at=datetime.now(UTC),
    )


def _make_hit(content: str = "How to rotate secrets", snippet: str | None = None) -> SopSearchHit:
    return SopSearchHit(sop=_make_sop(content=content), snippet=snippet)


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=SopService)


@pytest.fixture
def client(mock_service: AsyncMock) -> TestClient:
    app = create_app()
    app.dependency_overrides[sop_service_dependency] = lambda: mock_service
    app.dependency_overrides[get_current_service] = lambda: {
        "iss": "test-service", "aud": "offboardme-backend"
    }
    return TestClient(app)


class TestSearchSops:
    def test_200_returns_page(self, client: TestClient, mock_service: AsyncMock) -> None:
        hits = [_make_hit(snippet="How to <b>rotate</b> secrets"), _make_hit()]
        mock_service.search_sops.return_value = (hits, 2)

        r = client.get("/api/v1/sops")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2
        assert body["page"] == 1
        assert body["size"] == 20
        assert body["items"][0]["title"] == "Rotating secrets"
        assert body["items"][0]["snippet"] == "How to <b>rotate</b> secrets"
        assert body["items"][1]["snippet"] is None

    def test_200_empty_results(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.search_sops.return_value = ([], 0)

        r = client.get("/api/v1/sops?q=nothing")

        assert r.status_code == 200
        assert r.json()["total"] == 0
        assert r.json()["total_pages"] == 0

    def test_forwards_text_and_tags_query_params(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        mock_service.search_sops.return_value = ([], 0)

        r = client.get("/api/v1/sops?q=secrets&tags=security&tags=urgent&page=2&size=10")

        assert r.status_code == 200
        mock_service.search_sops.assert_awaited_once_with(
            text="secrets", tags=["security", "urgent"], page=2, size=10
        )

    def test_422_invalid_page(self, client: TestClient) -> None:
        r = client.get("/api/v1/sops?page=0")
        assert r.status_code == 422


class TestGetSop:
    def test_200_returns_sop(self, client: TestClient, mock_service: AsyncMock) -> None:
        sop = _make_sop()
        mock_service.get_sop.return_value = sop

        r = client.get(f"/api/v1/sops/{sop.sop_id.get_id()}")

        assert r.status_code == 200
        assert r.json()["id"] == str(sop.sop_id.get_id())
        assert r.json()["title"] == sop.title

    def test_404_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        sid = uuid4()
        mock_service.get_sop.side_effect = SopNotFoundError(str(sid))

        r = client.get(f"/api/v1/sops/{sid}")

        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_422_invalid_uuid(self, client: TestClient) -> None:
        r = client.get("/api/v1/sops/not-a-uuid")
        assert r.status_code == 422
