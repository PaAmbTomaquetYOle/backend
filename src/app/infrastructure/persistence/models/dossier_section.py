"""SQLModel persistence models for dossier sections and their child value-object tables."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, ForeignKey
from sqlmodel import Field, SQLModel

from app.domain.dossier.section import (
    Contact,
    ContactsSection,
    DossierSection,
    KnowledgeArea,
    KnowledgeAreasSection,
    PendingTask,
    PendingTasksSection,
    ResponsibilitiesSection,
)


class DossierSectionModel(SQLModel, table=True):
    """SQLModel persistence model for a dossier section."""

    __tablename__ = "dossier_sections"
    __table_args__ = (
        sa.UniqueConstraint(
            "dossier_id", "section_order", name="uq_dossier_sections_dossier_order"
        ),
        CheckConstraint(
            "section_type IN ('responsibilities','contacts','pending_tasks','knowledge_areas')",
            name="ck_dossier_sections_type",
        ),
        CheckConstraint(
            "section_order >= 0",
            name="ck_dossier_sections_order_positive",
        ),
    )

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    dossier_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("dossiers.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    title: str = Field(nullable=False)
    section_type: str = Field(nullable=False)
    section_order: int = Field(nullable=False)


class SectionResponsibilityModel(SQLModel, table=True):
    """SQLModel persistence model for a responsibility item within a responsibilities section."""

    __tablename__ = "section_responsibilities"
    __table_args__ = (
        CheckConstraint(
            "item_order >= 0",
            name="ck_section_responsibilities_order_positive",
        ),
    )

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    section_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("dossier_sections.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    description: str = Field(nullable=False)
    item_order: int = Field(nullable=False)


class SectionContactModel(SQLModel, table=True):
    """SQLModel persistence model for a contact item within a contacts section."""

    __tablename__ = "section_contacts"
    __table_args__ = (
        CheckConstraint(
            "email LIKE '%@%.%'",
            name="ck_section_contacts_email_format",
        ),
        CheckConstraint(
            "item_order >= 0",
            name="ck_section_contacts_order_positive",
        ),
    )

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    section_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("dossier_sections.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    name: str = Field(nullable=False)
    role: str = Field(nullable=False)
    email: str = Field(nullable=False)
    relationship: str = Field(nullable=False)
    item_order: int = Field(nullable=False)


class SectionPendingTaskModel(SQLModel, table=True):
    """SQLModel persistence model for a pending task item within a tasks section."""

    __tablename__ = "section_pending_tasks"
    __table_args__ = (
        CheckConstraint(
            "item_order >= 0",
            name="ck_section_pending_tasks_order_positive",
        ),
    )

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    section_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("dossier_sections.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    description: str = Field(nullable=False)
    priority: str = Field(nullable=False)
    deadline: str | None = Field(default=None)
    item_order: int = Field(nullable=False)


class SectionKnowledgeAreaModel(SQLModel, table=True):
    """SQLModel persistence model for a knowledge area item within a knowledge areas section."""

    __tablename__ = "section_knowledge_areas"
    __table_args__ = (
        CheckConstraint(
            "item_order >= 0",
            name="ck_section_knowledge_areas_order_positive",
        ),
    )

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    section_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("dossier_sections.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    topic: str = Field(nullable=False)
    description: str = Field(nullable=False)
    expertise_level: str = Field(nullable=False)
    item_order: int = Field(nullable=False)


def sections_from_domain(
    sections: list[DossierSection], dossier_id: uuid.UUID
) -> tuple[list[DossierSectionModel], list[SQLModel]]:
    """Convert domain sections to persistence models.

    Returns (section_models, child_item_models).
    Child items reference section_model.id, so section models must be flushed first.
    """
    section_models: list[DossierSectionModel] = []
    child_models: list[SQLModel] = []

    for order, section in enumerate(sections):
        section_model = DossierSectionModel(
            dossier_id=dossier_id,
            title=section.title,
            section_type=section.get_section_type(),
            section_order=order,
        )
        section_models.append(section_model)

        sid = section_model.id

        if isinstance(section, ResponsibilitiesSection):
            for i, desc in enumerate(section.responsibilities):
                child_models.append(
                    SectionResponsibilityModel(
                        section_id=sid, description=desc, item_order=i
                    )
                )
        elif isinstance(section, ContactsSection):
            for i, c in enumerate(section.contacts):
                child_models.append(
                    SectionContactModel(
                        section_id=sid,
                        name=c.name,
                        role=c.role,
                        email=c.email,
                        relationship=c.relationship,
                        item_order=i,
                    )
                )
        elif isinstance(section, PendingTasksSection):
            for i, t in enumerate(section.tasks):
                child_models.append(
                    SectionPendingTaskModel(
                        section_id=sid,
                        description=t.description,
                        priority=t.priority,
                        deadline=t.deadline,
                        item_order=i,
                    )
                )
        elif isinstance(section, KnowledgeAreasSection):
            for i, a in enumerate(section.areas):
                child_models.append(
                    SectionKnowledgeAreaModel(
                        section_id=sid,
                        topic=a.topic,
                        description=a.description,
                        expertise_level=a.expertise_level,
                        item_order=i,
                    )
                )

    return section_models, child_models


def sections_to_domain(
    section_models: list[DossierSectionModel],
    responsibilities: dict[uuid.UUID, list[SectionResponsibilityModel]],
    contacts: dict[uuid.UUID, list[SectionContactModel]],
    pending_tasks: dict[uuid.UUID, list[SectionPendingTaskModel]],
    knowledge_areas: dict[uuid.UUID, list[SectionKnowledgeAreaModel]],
) -> list[DossierSection]:
    """Reconstruct domain sections from persistence models."""
    result: list[DossierSection] = []

    for sm in sorted(section_models, key=lambda s: s.section_order):
        sid = sm.id
        if sm.section_type == "responsibilities":
            items = sorted(responsibilities.get(sid, []), key=lambda x: x.item_order)
            result.append(
                ResponsibilitiesSection(
                    title=sm.title,
                    responsibilities=[r.description for r in items],
                )
            )
        elif sm.section_type == "contacts":
            items = sorted(contacts.get(sid, []), key=lambda x: x.item_order)
            result.append(
                ContactsSection(
                    title=sm.title,
                    contacts=[
                        Contact(
                            name=c.name,
                            role=c.role,
                            email=c.email,
                            relationship=c.relationship,
                        )
                        for c in items
                    ],
                )
            )
        elif sm.section_type == "pending_tasks":
            items = sorted(pending_tasks.get(sid, []), key=lambda x: x.item_order)
            result.append(
                PendingTasksSection(
                    title=sm.title,
                    tasks=[
                        PendingTask(
                            description=t.description,
                            priority=t.priority,
                            deadline=t.deadline,
                        )
                        for t in items
                    ],
                )
            )
        elif sm.section_type == "knowledge_areas":
            items = sorted(knowledge_areas.get(sid, []), key=lambda x: x.item_order)
            result.append(
                KnowledgeAreasSection(
                    title=sm.title,
                    areas=[
                        KnowledgeArea(
                            topic=a.topic,
                            description=a.description,
                            expertise_level=a.expertise_level,
                        )
                        for a in items
                    ],
                )
            )

    return result
