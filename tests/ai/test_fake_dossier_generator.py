"""Tests for FakeDossierGenerator."""

from datetime import UTC, datetime

import pytest

from app.domain import (
    CompletedInterviewState,
    Interview,
    InterviewId,
    InterviewNote,
    InterviewQuestion,
    OffboardingProcessId,
    ResponsibilitiesSection,
    SpeakerRoleEnum,
)
from app.infrastructure.adapters.ai.fake_dossier_generator import FakeDossierGenerator


def _interview(turns: list) -> Interview:
    return Interview(
        interview_id=InterviewId(),
        process_id=OffboardingProcessId(),
        state=CompletedInterviewState(),
        scheduled_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        turns=turns,
    )


class TestFakeDossierGenerator:
    @pytest.mark.anyio
    async def test_builds_responsibilities_from_answered_questions(self) -> None:
        turns = [
            InterviewQuestion(
                speaker_role=SpeakerRoleEnum.INTERVIEWER,
                timestamp=datetime.now(UTC),
                content="What are your main responsibilities?",
                order=0,
                answer_text="Lead the backend team",
            ),
            InterviewQuestion(
                speaker_role=SpeakerRoleEnum.INTERVIEWER,
                timestamp=datetime.now(UTC),
                content="Anything else?",
                order=1,
                answer_text=None,
            ),
            InterviewNote(
                speaker_role=SpeakerRoleEnum.INTERVIEWEE,
                timestamp=datetime.now(UTC),
                content="Some free-form note",
                order=2,
            ),
        ]
        generator = FakeDossierGenerator()

        summary, sections = await generator.generate(_interview(turns))

        assert "1" in summary
        assert len(sections) == 1
        assert isinstance(sections[0], ResponsibilitiesSection)
        assert sections[0].responsibilities == ["Lead the backend team"]

    @pytest.mark.anyio
    async def test_no_answers_yields_no_sections(self) -> None:
        generator = FakeDossierGenerator()

        summary, sections = await generator.generate(_interview([]))

        assert sections == []
        assert "0" in summary
