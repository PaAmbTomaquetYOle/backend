"""Unit tests for SopRepository using in-memory async SQLite.

Text search falls back to a case-insensitive substring match on SQLite (no
to_tsvector support there) — see SopRepository._text_filter — so these tests
exercise that fallback path. Postgres full-text behavior is exercised only
when running against a real Postgres instance (not covered by this suite).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.domain.sops.sop import Sop
from app.infrastructure.adapters.repositories.sop import SopRepository
from app.infrastructure.persistence import models as _models  # noqa: F401 — registers tables


@pytest.fixture(name="engine")
async def engine_fixture():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(name="session")
async def session_fixture(engine):
    async with AsyncSession(engine) as session:
        yield session


@pytest.fixture(name="repository")
def repository_fixture(session):
    return SopRepository(session, dialect_name="sqlite")


def make_sop(
    content: str = "How to rotate secrets",
    tags: list[str] | None = None,
    title: str = "Rotating secrets",
) -> Sop:
    return Sop(
        sop_id=SopId(),
        title=title,
        content=content,
        author=AuthorId("U1"),
        tags=tags or [],
        origin_channel=ChannelId("C1"),
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.mark.anyio
class TestSaveAndFindById:
    async def test_save_and_find_by_id(self, repository):
        sop = make_sop(tags=["security"])
        await repository.save(sop)

        found = await repository.find_by_id(sop.sop_id)
        assert found is not None
        assert found.title == sop.title
        assert found.content == sop.content
        assert found.tags == ["security"]

    async def test_find_by_id_returns_none_when_not_found(self, repository):
        assert await repository.find_by_id(SopId()) is None

    async def test_find_by_id_returns_none_when_soft_deleted(self, repository):
        sop = make_sop()
        await repository.save(sop)
        sop.mark_deleted()
        await repository.save(sop)

        assert await repository.find_by_id(sop.sop_id) is None

    async def test_save_twice_updates_tags(self, repository):
        sop = make_sop(tags=["a", "b"])
        await repository.save(sop)
        sop.revise(tags=["c"])
        await repository.save(sop)

        found = await repository.find_by_id(sop.sop_id)
        assert found.tags == ["c"]
        assert found.version == 2


@pytest.mark.anyio
class TestSoftDelete:
    async def test_soft_deleted_sop_excluded_from_search(self, repository):
        sop = make_sop()
        await repository.save(sop)
        sop.mark_deleted()
        await repository.save(sop)

        items, total = await repository.search(text=None, tags=None, page=1, size=20)
        assert sop.sop_id.get_id() not in {i.sop.sop_id.get_id() for i in items}
        assert total == 0


@pytest.mark.anyio
class TestSearch:
    async def test_text_filter_matches_content_substring(self, repository):
        await repository.save(make_sop(content="How to rotate secrets"))
        await repository.save(make_sop(content="How to onboard a new hire"))

        items, total = await repository.search(text="rotate", tags=None, page=1, size=20)
        assert total == 1
        assert "rotate" in items[0].sop.content.lower()

    async def test_text_filter_matches_title_substring(self, repository):
        await repository.save(make_sop(title="Rotating secrets", content="unrelated body"))
        await repository.save(make_sop(title="Onboarding a new hire", content="unrelated body"))

        items, total = await repository.search(text="rotating", tags=None, page=1, size=20)
        assert total == 1
        assert "rotating" in items[0].sop.title.lower()

    async def test_sqlite_search_hit_has_no_snippet(self, repository):
        await repository.save(make_sop(content="How to rotate secrets"))

        items, _ = await repository.search(text="rotate", tags=None, page=1, size=20)
        assert items[0].snippet is None

    async def test_tag_filter_requires_all_tags(self, repository):
        await repository.save(make_sop(content="a", tags=["security", "urgent"]))
        await repository.save(make_sop(content="b", tags=["security"]))

        items, total = await repository.search(
            text=None, tags=["security", "urgent"], page=1, size=20
        )
        assert total == 1
        assert items[0].sop.content == "a"

    async def test_text_and_tags_combine_with_and(self, repository):
        await repository.save(make_sop(content="rotate secrets", tags=["security"]))
        await repository.save(make_sop(content="rotate secrets", tags=["other"]))

        items, total = await repository.search(text="rotate", tags=["security"], page=1, size=20)
        assert total == 1

    async def test_pagination(self, repository):
        for i in range(5):
            await repository.save(make_sop(content=f"doc {i}"))

        page1, total = await repository.search(text=None, tags=None, page=1, size=2)
        page2, _ = await repository.search(text=None, tags=None, page=2, size=2)

        assert total == 5
        assert len(page1) == 2
        assert len(page2) == 2
        assert {s.sop.sop_id.get_id() for s in page1}.isdisjoint(
            {s.sop.sop_id.get_id() for s in page2}
        )

    async def test_empty_search_returns_all_non_deleted(self, repository):
        await repository.save(make_sop())
        await repository.save(make_sop())

        items, total = await repository.search(text=None, tags=None, page=1, size=20)
        assert total == 2
        assert len(items) == 2
