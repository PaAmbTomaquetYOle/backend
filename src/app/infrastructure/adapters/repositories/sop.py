"""SQLModel-backed repository for SOPs."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, delete, select

from app.application.ports.sop import ISopRepository
from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.domain.sops.sop import Sop
from app.infrastructure.persistence.models.sop import SopModel
from app.infrastructure.persistence.models.tag import SopTagLink, TagModel


class SopRepository(ISopRepository):
    """SQLModel-backed implementation of ISopRepository.

    Text search uses Postgres full-text search (to_tsvector/plainto_tsquery)
    when running against Postgres. Against SQLite (used by the test suite,
    which has no to_tsvector support) it falls back to a case-insensitive
    substring match, so the same repository code is exercised in both cases.
    """

    def __init__(self, session: AsyncSession, dialect_name: str = "postgresql") -> None:
        """Initialize the repository with a database session.

        Args:
            session: The active SQLModel session to use for all queries.
            dialect_name: The SQL dialect in use ("postgresql" or "sqlite"),
                used to pick the text search strategy. Defaults to "postgresql".
        """
        self._session = session
        self._dialect_name = dialect_name

    async def save(self, sop: Sop) -> None:
        """Persist a SOP (insert or update), syncing its tags."""
        model = SopModel(
            id=sop.sop_id.get_id(),
            content=sop.content,
            author=sop.author.get_id(),
            origin_channel=sop.origin_channel.get_id(),
            version=sop.version,
            created_at=sop.created_at,
            updated_at=sop.updated_at,
            deleted_at=sop.deleted_at,
        )
        await self._session.merge(model)
        await self._session.flush()
        await self._sync_tags(sop.sop_id.get_id(), sop.tags)
        await self._session.commit()

    async def _sync_tags(self, sop_id, tags: list[str]) -> None:
        """Replace the tag links for a SOP with the given tag names.

        Creates any tags that don't already exist yet (by name).
        """
        await self._session.execute(
            delete(SopTagLink).where(col(SopTagLink.sop_id) == sop_id)
        )
        for name in tags:
            tag = (
                await self._session.execute(
                    select(TagModel).where(col(TagModel.name) == name)
                )
            ).scalars().first()
            if tag is None:
                tag = TagModel(name=name)
                self._session.add(tag)
                await self._session.flush()
            self._session.add(SopTagLink(sop_id=sop_id, tag_id=tag.id))
        await self._session.flush()

    async def find_by_id(self, sop_id: SopId) -> Sop | None:
        """Return the non-deleted SOP with the given ID, or None if not found."""
        model = await self._session.get(SopModel, sop_id.get_id())
        if model is None or model.deleted_at is not None:
            return None
        return await self._to_domain(model)

    async def search(
        self,
        text: str | None,
        tags: list[str] | None,
        page: int,
        size: int,
    ) -> tuple[list[Sop], int]:
        """Search non-deleted SOPs by full-text query and/or tags (match-all)."""
        stmt = select(SopModel).where(col(SopModel.deleted_at).is_(None))

        if text:
            stmt = stmt.where(self._text_filter(text))

        if tags:
            stmt = (
                stmt.join(SopTagLink, col(SopTagLink.sop_id) == col(SopModel.id))
                .join(TagModel, col(TagModel.id) == col(SopTagLink.tag_id))
                .where(col(TagModel.name).in_(tags))
                .group_by(col(SopModel.id))
                .having(func.count(func.distinct(TagModel.name)) == len(tags))
            )

        total = len((await self._session.execute(stmt)).scalars().all())
        page_stmt = stmt.offset((page - 1) * size).limit(size)
        rows = (await self._session.execute(page_stmt)).scalars().all()
        return [await self._to_domain(model) for model in rows], total

    def _text_filter(self, text: str):
        """Build the text-matching predicate for the active dialect."""
        if self._dialect_name == "postgresql":
            return func.to_tsvector("english", col(SopModel.content)).op("@@")(
                func.plainto_tsquery("english", text)
            )
        return col(SopModel.content).ilike(f"%{text}%")

    async def _to_domain(self, model: SopModel) -> Sop:
        """Reconstruct a domain Sop from its persistence model, including tags."""
        tag_rows = (
            await self._session.execute(
                select(TagModel.name)
                .join(SopTagLink, col(SopTagLink.tag_id) == col(TagModel.id))
                .where(col(SopTagLink.sop_id) == model.id)
            )
        ).scalars().all()
        return Sop(
            sop_id=SopId(model.id),
            content=model.content,
            author=AuthorId(model.author),
            tags=list(tag_rows),
            origin_channel=ChannelId(model.origin_channel),
            created_at=model.created_at,
            version=model.version,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
