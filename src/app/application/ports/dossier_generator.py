"""Dossier generator port — abstract interface for producing dossier content."""

from abc import ABC, abstractmethod
from typing import Literal

from app.domain.dossier.section import DossierSection
from app.domain.interview.interview import Interview

DossierScope = Literal["offboarding", "monthly", "annual"]


class IDossierGenerator(ABC):
    """Abstract interface for generating dossier content from a completed interview.

    Implementations decide how the summary and sections are produced (a fixed
    template, a deterministic transformation, an LLM call, ...); callers only
    depend on this port, so the strategy can be swapped without touching the
    orchestration logic (Dependency Inversion).
    """

    @abstractmethod
    async def generate(
        self, interview: Interview, scope: DossierScope = "offboarding"
    ) -> tuple[str | None, list[DossierSection]]:
        """Generate dossier content from a completed interview.

        Args:
            interview: The completed interview to derive dossier content from.
            scope: Which kind of dossier to write — "offboarding" (default,
                a departing employee's handover), "monthly" (lightweight
                knowledge-retention check-in), or "annual" (exhaustive
                knowledge-retention review). Mirrors mcp-server's
                'generate_dossier' tool 'review_scope' parameter (MCP-15).

        Returns:
            A tuple of (summary, sections) to persist on the dossier.
        """
