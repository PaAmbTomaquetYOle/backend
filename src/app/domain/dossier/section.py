"""Dossier section value objects."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Contact:
    """Immutable value object representing a key contact."""

    def __init__(self, name: str, role: str, email: str, relationship: str) -> None:
        self.__name = name
        self.__role = role
        self.__email = email
        self.__relationship = relationship

    @property
    def name(self) -> str:
        return self.__name

    @property
    def role(self) -> str:
        return self.__role

    @property
    def email(self) -> str:
        return self.__email

    @property
    def relationship(self) -> str:
        return self.__relationship


class PendingTask:
    """Immutable value object representing an open task requiring handover."""

    def __init__(self, description: str, priority: str, deadline: str | None = None) -> None:
        self.__description = description
        self.__priority = priority
        self.__deadline = deadline

    @property
    def description(self) -> str:
        return self.__description

    @property
    def priority(self) -> str:
        return self.__priority

    @property
    def deadline(self) -> str | None:
        return self.__deadline


class KnowledgeArea:
    """Immutable value object representing a critical knowledge area."""

    def __init__(self, topic: str, description: str, expertise_level: str) -> None:
        self.__topic = topic
        self.__description = description
        self.__expertise_level = expertise_level

    @property
    def topic(self) -> str:
        return self.__topic

    @property
    def description(self) -> str:
        return self.__description

    @property
    def expertise_level(self) -> str:
        return self.__expertise_level


class DossierSection(ABC):
    """Abstract base class for a dossier section."""

    def __init__(self, title: str) -> None:
        self.__title = title

    @property
    def title(self) -> str:
        return self.__title

    @abstractmethod
    def get_section_type(self) -> str:
        """Returns a discriminator string identifying the section type."""


class ResponsibilitiesSection(DossierSection):
    """Key responsibilities the departing employee held."""

    def __init__(self, title: str, responsibilities: list[str]) -> None:
        super().__init__(title)
        self.__responsibilities = responsibilities

    @property
    def responsibilities(self) -> list[str]:
        return list(self.__responsibilities)

    def get_section_type(self) -> str:
        return "responsibilities"


class ContactsSection(DossierSection):
    """Key internal/external contacts the successor should know."""

    def __init__(self, title: str, contacts: list[Contact]) -> None:
        super().__init__(title)
        self.__contacts = contacts

    @property
    def contacts(self) -> list[Contact]:
        return list(self.__contacts)

    def get_section_type(self) -> str:
        return "contacts"


class PendingTasksSection(DossierSection):
    """Tasks still open or in-progress that need handover."""

    def __init__(self, title: str, tasks: list[PendingTask]) -> None:
        super().__init__(title)
        self.__tasks = tasks

    @property
    def tasks(self) -> list[PendingTask]:
        return list(self.__tasks)

    def get_section_type(self) -> str:
        return "pending_tasks"


class KnowledgeAreasSection(DossierSection):
    """Critical knowledge areas and documentation pointers."""

    def __init__(self, title: str, areas: list[KnowledgeArea]) -> None:
        super().__init__(title)
        self.__areas = areas

    @property
    def areas(self) -> list[KnowledgeArea]:
        return list(self.__areas)

    def get_section_type(self) -> str:
        return "knowledge_areas"
