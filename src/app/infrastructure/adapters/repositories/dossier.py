"""SQLModel-backed repository for dossiers."""

from __future__ import annotations

import uuid
from collections import defaultdict

from sqlmodel import Session, col, select

from app.application.ports.dossier import IDossierRepository
from app.domain.dossier.dossier import Dossier
from app.domain.offboarding.id import DossierId, InterviewId, OffboardingProcessId
from app.infrastructure.persistence.models.dossier import DossierModel
from app.infrastructure.persistence.models.dossier_section import (
    DossierSectionModel,
    SectionContactModel,
    SectionKnowledgeAreaModel,
    SectionPendingTaskModel,
    SectionResponsibilityModel,
    sections_from_domain,
    sections_to_domain,
)


class DossierRepository(IDossierRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, dossier: Dossier) -> None:
        model = DossierModel.from_domain(dossier)
        self._session.merge(model)
        self._session.flush()

        self._delete_sections(model.id)

        section_models, child_models = sections_from_domain(
            dossier.sections, model.id
        )
        for sm in section_models:
            self._session.add(sm)
        self._session.flush()
        for cm in child_models:
            self._session.add(cm)

        self._session.commit()

    def find_by_id(self, dossier_id: DossierId) -> Dossier | None:
        model = self._session.get(DossierModel, dossier_id.get_id())
        if not model:
            return None
        return self._load_with_sections(model)

    def find_by_process_id(self, process_id: OffboardingProcessId) -> Dossier | None:
        model = self._session.exec(
            select(DossierModel).where(
                col(DossierModel.process_id) == process_id.get_id()
            )
        ).first()
        if not model:
            return None
        return self._load_with_sections(model)

    def find_by_interview_id(self, interview_id: InterviewId) -> Dossier | None:
        model = self._session.exec(
            select(DossierModel).where(
                col(DossierModel.interview_id) == interview_id.get_id()
            )
        ).first()
        if not model:
            return None
        return self._load_with_sections(model)

    def find_all(self) -> list[Dossier]:
        models = self._session.exec(select(DossierModel)).all()
        return [self._load_with_sections(m) for m in models]

    def delete(self, dossier_id: DossierId) -> None:
        model = self._session.get(DossierModel, dossier_id.get_id())
        if model:
            self._session.delete(model)
            self._session.commit()

    def _load_with_sections(self, model: DossierModel) -> Dossier:
        section_models = list(
            self._session.exec(
                select(DossierSectionModel).where(
                    col(DossierSectionModel.dossier_id) == model.id
                )
            ).all()
        )

        section_ids = [s.id for s in section_models]
        if not section_ids:
            return model.to_domain(sections=[])

        responsibilities = self._group_by_section(
            SectionResponsibilityModel, section_ids
        )
        contacts = self._group_by_section(SectionContactModel, section_ids)
        pending_tasks = self._group_by_section(SectionPendingTaskModel, section_ids)
        knowledge_areas = self._group_by_section(
            SectionKnowledgeAreaModel, section_ids
        )

        domain_sections = sections_to_domain(
            section_models, responsibilities, contacts, pending_tasks, knowledge_areas
        )
        return model.to_domain(sections=domain_sections)

    def _group_by_section(
        self, model_cls: type, section_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list]:
        rows = self._session.exec(
            select(model_cls).where(model_cls.section_id.in_(section_ids))  # type: ignore[attr-defined]
        ).all()
        grouped: dict[uuid.UUID, list] = defaultdict(list)
        for row in rows:
            grouped[row.section_id].append(row)
        return grouped

    def _delete_sections(self, dossier_id: uuid.UUID) -> None:
        existing = self._session.exec(
            select(DossierSectionModel).where(
                col(DossierSectionModel.dossier_id) == dossier_id
            )
        ).all()
        for section in existing:
            self._session.delete(section)
        self._session.flush()
