from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, EmailStr, model_validator

from app.domain import (
    Contact,
    ContactsSection,
    Dossier,
    DossierSection,
    KnowledgeArea,
    KnowledgeAreasSection,
    PendingTask,
    PendingTasksSection,
    ResponsibilitiesSection,
)


class ContactSchema(BaseModel):
    name: str
    role: str
    email: EmailStr
    relationship: str


class PendingTaskSchema(BaseModel):
    description: str
    priority: str
    deadline: str | None = None


class KnowledgeAreaSchema(BaseModel):
    topic: str
    description: str
    expertise_level: str


class DossierSectionRequest(BaseModel):
    title: str
    section_type: Literal["responsibilities", "contacts", "pending_tasks", "knowledge_areas"]
    responsibilities: list[str] | None = None
    contacts: list[ContactSchema] | None = None
    tasks: list[PendingTaskSchema] | None = None
    areas: list[KnowledgeAreaSchema] | None = None

    @model_validator(mode="after")
    def validate_section_data(self) -> Self:
        expected = {
            "responsibilities": "responsibilities",
            "contacts": "contacts",
            "pending_tasks": "tasks",
            "knowledge_areas": "areas",
        }
        field = expected[self.section_type]
        if getattr(self, field) is None:
            raise ValueError(f"Field '{field}' is required for section_type '{self.section_type}'")
        other_fields = [f for f in expected.values() if f != field]
        for f in other_fields:
            if getattr(self, f) is not None:
                raise ValueError(
                    f"Field '{f}' must be null for section_type '{self.section_type}'"
                )
        return self

    def to_domain(self) -> DossierSection:
        if self.section_type == "responsibilities":
            return ResponsibilitiesSection(title=self.title, responsibilities=self.responsibilities)
        if self.section_type == "contacts":
            return ContactsSection(
                title=self.title,
                contacts=[Contact(c.name, c.role, c.email, c.relationship) for c in self.contacts],
            )
        if self.section_type == "pending_tasks":
            return PendingTasksSection(
                title=self.title,
                tasks=[PendingTask(t.description, t.priority, t.deadline) for t in self.tasks],
            )
        return KnowledgeAreasSection(
            title=self.title,
            areas=[KnowledgeArea(a.topic, a.description, a.expertise_level) for a in self.areas],
        )


class CreateDossierRequest(BaseModel):
    summary: str | None = None
    sections: list[DossierSectionRequest] = []


class DossierSectionResponse(BaseModel):
    title: str
    section_type: str
    responsibilities: list[str] | None = None
    contacts: list[ContactSchema] | None = None
    tasks: list[PendingTaskSchema] | None = None
    areas: list[KnowledgeAreaSchema] | None = None


class DossierResponse(BaseModel):
    id: UUID
    process_id: UUID
    interview_id: UUID
    state: str
    created_at: datetime
    summary: str | None
    sections: list[DossierSectionResponse]


def _section_to_response(section: DossierSection) -> DossierSectionResponse:
    responsibilities = None
    contacts = None
    tasks = None
    areas = None
    if isinstance(section, ResponsibilitiesSection):
        responsibilities = section.responsibilities
    elif isinstance(section, ContactsSection):
        contacts = [
            ContactSchema(name=c.name, role=c.role, email=c.email, relationship=c.relationship)
            for c in section.contacts
        ]
    elif isinstance(section, PendingTasksSection):
        tasks = [
            PendingTaskSchema(description=t.description, priority=t.priority, deadline=t.deadline)
            for t in section.tasks
        ]
    elif isinstance(section, KnowledgeAreasSection):
        areas = [
            KnowledgeAreaSchema(topic=a.topic, description=a.description, expertise_level=a.expertise_level)
            for a in section.areas
        ]
    return DossierSectionResponse(
        title=section.title,
        section_type=section.get_section_type(),
        responsibilities=responsibilities,
        contacts=contacts,
        tasks=tasks,
        areas=areas,
    )


def dossier_to_response(dossier: Dossier) -> DossierResponse:
    return DossierResponse(
        id=dossier.dossier_id.get_id(),
        process_id=dossier.process_id.get_id(),
        interview_id=dossier.interview_id.get_id(),
        state=dossier.state.get_state().value,
        created_at=dossier.created_at,
        summary=dossier.summary,
        sections=[_section_to_response(s) for s in dossier.sections],
    )
