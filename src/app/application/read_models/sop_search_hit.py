"""Read model for a single SOP search result."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.sops.sop import Sop


@dataclass(frozen=True)
class SopSearchHit:
    """A SOP matched by a search, together with its search-only presentation data.

    ``snippet`` is a full-text-search highlight (Postgres ``ts_headline``), not
    a property of the SOP itself, so it lives here rather than on the domain
    entity. It is None when the search had no text query (Postgres) or when
    running against SQLite, which has no FTS support.
    """

    sop: Sop
    snippet: str | None
