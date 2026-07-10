"""Dossier generator port — abstract interface for producing dossier content."""

from abc import ABC, abstractmethod

from app.domain.dossier.section import DossierSection
from app.domain.interview.interview import Interview


class IDossierGenerator(ABC):
    """Abstract interface for generating dossier content from a completed interview.

    Implementations decide how the summary and sections are produced (a fixed
    template, a deterministic transformation, an LLM call, ...); callers only
    depend on this port, so the strategy can be swapped without touching the
    orchestration logic (Dependency Inversion).
    """

    @abstractmethod
    async def generate(self, interview: Interview) -> tuple[str | None, list[DossierSection]]:
        """Generate dossier content from a completed interview.

        Args:
            interview: The completed interview to derive dossier content from.

        Returns:
            A tuple of (summary, sections) to persist on the dossier.
        """
