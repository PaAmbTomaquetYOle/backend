"""Unit tests for SOP API endpoints — mock service, test HTTP layer only."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

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
        content=content,
        author=AuthorId("U1"),
        tags=tags or ["security"],
        origin_channel=ChannelId("C1"),
        created_at=datetime.now(UTC),
    )


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


class TestCreateSop:
    def test_201_returns_sop(self, client: TestClient, mock_service: AsyncMock) -> None:
        sop = _make_sop()
        mock_service.create_sop.return_value = sop

        r = client.post("/api/v1/sops", json={
            "content": sop.content,
            "author": "U1",
            "origin_channel": "C1",
            "tags": ["security"],
        })

        assert r.status_code == 201
        body = r.json()
        assert body["id"] == str(sop.sop_id.get_id())
        assert body["version"] == 1

    def test_422_missing_content(self, client: TestClient) -> None:
        r = client.post("/api/v1/sops", json={"author": "U1", "origin_channel": "C1"})
        assert r.status_code == 422


class TestSearchSops:
    def test_200_returns_page(self, client: TestClient, mock_service: AsyncMock) -> None:
        sops = [_make_sop(), _make_sop()]
        mock_service.search_sops.return_value = (sops, 2)

        r = client.get("/api/v1/sops")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2
        assert body["page"] == 1
        assert body["size"] == 20

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

    def test_404_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        sid = uuid4()
        mock_service.get_sop.side_effect = SopNotFoundError(str(sid))

        r = client.get(f"/api/v1/sops/{sid}")

        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_422_invalid_uuid(self, client: TestClient) -> None:
        r = client.get("/api/v1/sops/not-a-uuid")
        assert r.status_code == 422


class TestUpdateSop:
    def test_200_returns_updated_sop(self, client: TestClient, mock_service: AsyncMock) -> None:
        sop = _make_sop(content="revised")
        mock_service.update_sop.return_value = sop

        r = client.patch(f"/api/v1/sops/{uuid4()}", json={"content": "revised"})

        assert r.status_code == 200
        assert r.json()["content"] == "revised"

    def test_404_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        sid = uuid4()
        mock_service.update_sop.side_effect = SopNotFoundError(str(sid))

        r = client.patch(f"/api/v1/sops/{sid}", json={"content": "x"})

        assert r.status_code == 404

    def test_partial_update_omits_unset_fields(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        mock_service.update_sop.return_value = _make_sop()

        r = client.patch(f"/api/v1/sops/{uuid4()}", json={"tags": ["new"]})

        assert r.status_code == 200
        _, kwargs = mock_service.update_sop.call_args
        assert kwargs["content"] is None
        assert kwargs["tags"] == ["new"]


class TestDeleteSop:
    def test_204_on_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.delete_sop.return_value = None

        r = client.delete(f"/api/v1/sops/{uuid4()}")

        assert r.status_code == 204

    def test_404_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        sid = uuid4()
        mock_service.delete_sop.side_effect = SopNotFoundError(str(sid))

        r = client.delete(f"/api/v1/sops/{sid}")

        assert r.status_code == 404
