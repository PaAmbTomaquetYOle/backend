"""Unit tests for SopCandidateRepository using in-memory async SQLite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from app.domain.sops.candidate import SopCandidate
from app.domain.sops.id import AuthorId, ChannelId, SopCandidateId
from app.infrastructure.adapters.repositories.sop_candidate import SopCandidateRepository
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
    return SopCandidateRepository(session)


def make_candidate(
    channel_id: str = "C1", message_ts: str = "1720000000.000100"
) -> SopCandidate:
    return SopCandidate(
        candidate_id=SopCandidateId(),
        channel_id=ChannelId(channel_id),
        author_id=AuthorId("U1"),
        message_ts=message_ts,
        content="Rotate secrets every 90 days",
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.mark.anyio
class TestSaveAndFind:
    async def test_save_and_find_by_channel_and_ts(self, repository):
        candidate = make_candidate()
        await repository.save(candidate)

        found = await repository.find_by_channel_and_ts(candidate.channel_id, candidate.message_ts)
        assert found is not None
        assert found.content == candidate.content
        assert found.status == candidate.status

    async def test_find_by_channel_and_ts_returns_none_when_not_found(self, repository):
        found = await repository.find_by_channel_and_ts(ChannelId("C-unknown"), "0")
        assert found is None

    async def test_save_twice_updates_status(self, repository):
        candidate = make_candidate()
        await repository.save(candidate)
        candidate.mark_accepted()
        await repository.save(candidate)

        found = await repository.find_by_channel_and_ts(candidate.channel_id, candidate.message_ts)
        assert found.status.value == "accepted"


@pytest.mark.anyio
class TestFindPending:
    async def test_returns_only_offered_candidates(self, repository):
        pending = make_candidate(message_ts="1")
        decided = make_candidate(message_ts="2")
        await repository.save(pending)
        await repository.save(decided)
        decided.mark_rejected()
        await repository.save(decided)

        results = await repository.find_pending()

        assert {c.message_ts for c in results} == {"1"}

    async def test_returns_empty_list_when_none_pending(self, repository):
        assert await repository.find_pending() == []
