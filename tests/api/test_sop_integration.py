"""Integration tests for SOP endpoints — full stack with async in-memory SQLite DB.

The full SOP write lifecycle (create/update/delete) is Kafka-only (BE-21), so
test data is seeded directly via ``SopRepository`` — mirroring what the Kafka
handlers would persist — instead of through REST. This module exercises the
surviving read-only REST endpoints (search, get).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.domain.sops.sop import Sop
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.adapters.repositories.sop import SopRepository
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
    app = create_app()

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


async def _seed_sop(
    engine, content: str = "How to rotate secrets", tags=None, title: str = "Rotating secrets"
) -> Sop:
    sop = Sop(
        sop_id=SopId(),
        title=title,
        content=content,
        author=AuthorId("U1"),
        tags=tags or ["security"],
        origin_channel=ChannelId("C1"),
        created_at=datetime.now(UTC),
    )
    async with AsyncSession(engine) as session:
        await SopRepository(session, dialect_name="sqlite").save(sop)
    return sop


class TestSopCRUD:
    async def test_get_returns_200(self, client: httpx.AsyncClient, engine) -> None:
        sop = await _seed_sop(engine)

        r = await client.get(f"/api/v1/sops/{sop.sop_id.get_id()}")

        assert r.status_code == 200
        assert r.json()["id"] == str(sop.sop_id.get_id())
        assert r.json()["title"] == sop.title

    async def test_get_404_unknown_id(self, client: httpx.AsyncClient) -> None:
        r = await client.get(f"/api/v1/sops/{uuid4()}")
        assert r.status_code == 404


class TestSopSearch:
    async def test_search_all_paginated(self, client: httpx.AsyncClient, engine) -> None:
        for i in range(3):
            await _seed_sop(engine, content=f"doc {i}")

        r = await client.get("/api/v1/sops?page=1&size=2")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
        assert body["total_pages"] == 2

    async def test_search_by_text(self, client: httpx.AsyncClient, engine) -> None:
        await _seed_sop(engine, content="How to rotate secrets")
        await _seed_sop(engine, content="How to onboard a new hire")

        r = await client.get("/api/v1/sops?q=rotate")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert "rotate" in body["items"][0]["content"].lower()
        assert body["items"][0]["snippet"] is None  # sqlite has no ts_headline support

    async def test_search_by_title(self, client: httpx.AsyncClient, engine) -> None:
        await _seed_sop(engine, title="Rotating secrets", content="unrelated body")
        await _seed_sop(engine, title="Onboarding a new hire", content="unrelated body")

        r = await client.get("/api/v1/sops?q=rotating")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert "rotating" in body["items"][0]["title"].lower()

    async def test_search_by_tags_match_all(self, client: httpx.AsyncClient, engine) -> None:
        await _seed_sop(engine, content="a", tags=["security", "urgent"])
        await _seed_sop(engine, content="b", tags=["security"])

        r = await client.get("/api/v1/sops?tags=security&tags=urgent")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["items"][0]["content"] == "a"

    async def test_deleted_sops_excluded_from_search(
        self, client: httpx.AsyncClient, engine
    ) -> None:
        sop = await _seed_sop(engine)
        sop.mark_deleted()
        async with AsyncSession(engine) as session:
            await SopRepository(session, dialect_name="sqlite").save(sop)

        r = await client.get("/api/v1/sops")

        assert r.status_code == 200
        assert str(sop.sop_id.get_id()) not in [i["id"] for i in r.json()["items"]]
