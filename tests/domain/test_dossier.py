"""Unit tests for the Dossier aggregate root."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.domain.dossier.dossier import Dossier
from app.domain.dossier.section import ResponsibilitiesSection
from app.domain.dossier.state.not_generated import NotGeneratedDossierState
from app.domain.enums import DossierStateEnum, InterviewStateEnum
from app.domain.exceptions.dossier import DossierInterviewNotCompletedError
from app.domain.offboarding.id import DossierId, InterviewId, OffboardingProcessId

DT = datetime(2024, 1, 1, 12, 0, 0)


def make_dossier(state=None) -> Dossier:
    return Dossier(
        dossier_id=DossierId(),
        process_id=OffboardingProcessId(),
        interview_id=InterviewId(),
        state=state or NotGeneratedDossierState(),
        created_at=DT,
    )


class TestDossierConstruction:
    def test_properties_are_accessible(self):
        dossier_id = DossierId()
        process_id = OffboardingProcessId()
        interview_id = InterviewId()
        dossier = Dossier(
            dossier_id=dossier_id,
            process_id=process_id,
            interview_id=interview_id,
            state=NotGeneratedDossierState(),
            created_at=DT,
        )
        assert dossier.dossier_id is dossier_id
        assert dossier.process_id is process_id
        assert dossier.interview_id is interview_id
        assert dossier.created_at == DT
        assert dossier.state.get_state() == DossierStateEnum.NOT_GENERATED
        assert dossier.summary is None
        assert dossier.sections == []


class TestDossierStartGenerating:
    def test_start_generating_with_completed_interview(self):
        dossier = make_dossier()
        dossier.start_generating(InterviewStateEnum.COMPLETED)
        assert dossier.state.get_state() == DossierStateEnum.GENERATING

    def test_start_generating_with_in_progress_interview_raises(self):
        dossier = make_dossier()
        with pytest.raises(DossierInterviewNotCompletedError):
            dossier.start_generating(InterviewStateEnum.IN_PROGRESS)

    def test_start_generating_with_scheduled_interview_raises(self):
        dossier = make_dossier()
        with pytest.raises(DossierInterviewNotCompletedError):
            dossier.start_generating(InterviewStateEnum.SCHEDULED)


class TestDossierSummary:
    def test_summary_setter_works(self):
        dossier = make_dossier()
        dossier.summary = "This is a summary."
        assert dossier.summary == "This is a summary."


class TestDossierSections:
    def test_add_section_appends_section(self):
        dossier = make_dossier()
        section = ResponsibilitiesSection(
            title="Responsibilities", responsibilities=["Deploy code"]
        )
        dossier.add_section(section)
        assert section in dossier.sections

    def test_sections_returns_defensive_copy(self):
        dossier = make_dossier()
        section = ResponsibilitiesSection(
            title="Responsibilities", responsibilities=["Deploy code"]
        )
        dossier.add_section(section)
        sections_copy = dossier.sections
        sections_copy.clear()
        assert len(dossier.sections) == 1


class TestDossierIdSetter:
    def test_dossier_id_setter_works(self):
        dossier = make_dossier()
        new_id = DossierId()
        dossier.dossier_id = new_id
        assert dossier.dossier_id is new_id
