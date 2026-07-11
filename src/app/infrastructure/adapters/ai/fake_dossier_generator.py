"""Deterministic placeholder implementation of IDossierGenerator.

Builds dossier content directly from the interview's answered questions, with
no external LLM call. This closes the Kafka consumer cycle end to end while a
real LLM-backed adapter is built separately (see IDossierGenerator).
"""

from app.application.ports.dossier_generator import DossierScope, IDossierGenerator
from app.domain.dossier.section import DossierSection, ResponsibilitiesSection
from app.domain.interview.interview import Interview
from app.domain.interview.turn import InterviewQuestion


class FakeDossierGenerator(IDossierGenerator):
    """Deterministically derives a summary and a responsibilities section from
    the answered questions of a completed interview."""

    async def generate(
        self, interview: Interview, scope: DossierScope = "offboarding"
    ) -> tuple[str | None, list[DossierSection]]:
        """Generate dossier content from the interview's question/answer turns.

        Args:
            interview: The completed interview to derive dossier content from.
            scope: Unused — the fake generator produces the same deterministic
                output regardless of scope.

        Returns:
            A tuple of (summary, sections). The summary counts the answered
            questions; the sole section lists each answer as a responsibility.
        """
        answers = [
            turn.answer_text
            for turn in interview.turns
            if isinstance(turn, InterviewQuestion) and turn.answer_text
        ]
        summary = (
            f"Auto-generated dossier from {len(answers)} answered interview question(s)."
        )
        sections: list[DossierSection] = []
        if answers:
            sections.append(
                ResponsibilitiesSection(title="Responsibilities", responsibilities=answers)
            )
        return summary, sections
