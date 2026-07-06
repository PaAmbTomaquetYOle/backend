"""SQLModel-backed repository for dossiers."""

from __future__ import annotations

import uuid
from collections import defaultdict

from sqlmodel import Session, col, select

from app.application.ports.dossier import DossierSearchResult, IDossierRepository
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
from app.infrastructure.persistence.models.process import ProcessModel


class DossierRepository(IDossierRepository):
    """SQLModel-backed implementation of IDossierRepository."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The active SQLModel session to use for all queries.
        """
        self._session = session

    def save(self, dossier: Dossier) -> None:
        """Persist a dossier and all its sections (insert or update)."""
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
        """Return the dossier with the given ID, or None if not found."""
        # noinspection PyTypeChecker
        model: DossierModel | None = self._session.get(DossierModel, dossier_id.get_id())
        if not model:
            return None
        return self._load_with_sections(model)

    def find_by_process_id(self, process_id: OffboardingProcessId) -> Dossier | None:
        """Return the dossier for the given process, or None if not found."""
        model: DossierModel | None = self._session.exec(
            select(DossierModel).where(
                col(DossierModel.process_id) == process_id.get_id()
            )
        ).first()
        if not model:
            return None
        return self._load_with_sections(model)

    def find_by_interview_id(self, interview_id: InterviewId) -> Dossier | None:
        """Return the dossier for the given interview, or None if not found."""
        model: DossierModel | None = self._session.exec(
            select(DossierModel).where(
                col(DossierModel.interview_id) == interview_id.get_id()
            )
        ).first()
        if not model:
            return None
        return self._load_with_sections(model)

    def find_all(self) -> list[Dossier]:
        """Return all stored dossiers."""
        models = self._session.exec(select(DossierModel)).all()
        return [self._load_with_sections(m) for m in models]

    def search(
        self,
        employee_name: str | None = None,
        process_id: uuid.UUID | None = None,
    ) -> list[DossierSearchResult]:
        """Search dossiers by employee display name and/or process ID."""
        stmt = select(DossierModel, ProcessModel).join(
            ProcessModel, col(DossierModel.process_id) == col(ProcessModel.id)
        )
        if employee_name is not None:
            stmt = stmt.where(col(ProcessModel.employee_name).ilike(f"%{employee_name}%"))
        if process_id is not None:
            stmt = stmt.where(col(DossierModel.process_id) == process_id)
        rows = self._session.exec(stmt).all()
        return [
            DossierSearchResult(
                dossier=self._load_with_sections(dossier_model),
                employee_id=process_model.employee_id,
                manager_id=process_model.manager_id,
                employee_name=process_model.employee_name,
                manager_name=process_model.manager_name,
            )
            for dossier_model, process_model in rows
        ]

    def delete(self, dossier_id: DossierId) -> None:
        """Remove the dossier with the given ID (no-op if not found)."""
        model = self._session.get(DossierModel, dossier_id.get_id())
        if model:
            self._session.delete(model)
            self._session.commit()

    def _load_with_sections(self, model: DossierModel) -> Dossier:
        """Reconstruct a domain Dossier from a DossierModel by loading all its sections from the DB.

        Args:
            model: The DossierModel whose sections should be loaded.

        Returns:
            Dossier: The fully reconstructed domain aggregate with all sections.
        """
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
        """Query child item models grouped by their parent section ID.

        Args:
            model_cls: The SQLModel class for the child item table.
            section_ids: List of section UUIDs to fetch children for.

        Returns:
            dict[uuid.UUID, list]: Mapping from section_id to list of child model instances.
        """
        rows = self._session.exec(
            select(model_cls).where(model_cls.section_id.in_(section_ids))  # type: ignore[attr-defined]
        ).all()
        grouped: dict[uuid.UUID, list] = defaultdict(list)
        for row in rows:
            grouped[row.section_id].append(row)
        return grouped

    def _delete_sections(self, dossier_id: uuid.UUID) -> None:
        """Delete all section and child item rows belonging to the given dossier.

        Args:
            dossier_id: The UUID of the dossier whose sections should be removed.
        """
        existing = self._session.exec(
            select(DossierSectionModel).where(
                col(DossierSectionModel.dossier_id) == dossier_id
            )
        ).all()
        for section in existing:
            self._session.delete(section)
        self._session.flush()
