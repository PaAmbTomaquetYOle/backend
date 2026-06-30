"""Dossier section value objects."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Contact:
    """Immutable value object representing a key contact."""

    def __init__(self, name: str, role: str, email: str, relationship: str) -> None:
        """Initialize the contact value object.

        Args:
            name: Full name of the contact.
            role: Job title or role of the contact.
            email: Email address of the contact.
            relationship: How this contact relates to the departing employee.
        """
        self.__name = name
        self.__role = role
        self.__email = email
        self.__relationship = relationship

    @property
    def name(self) -> str:
        """Full name of the contact."""
        return self.__name

    @property
    def role(self) -> str:
        """Job title or role of the contact."""
        return self.__role

    @property
    def email(self) -> str:
        """Email address of the contact."""
        return self.__email

    @property
    def relationship(self) -> str:
        """How this contact relates to the departing employee."""
        return self.__relationship


class PendingTask:
    """Immutable value object representing an open task requiring handover."""

    def __init__(self, description: str, priority: str, deadline: str | None = None) -> None:
        """Initialize the pending task value object.

        Args:
            description: Description of the task that needs handover.
            priority: Priority level of the task (e.g., 'high', 'medium', 'low').
            deadline: Optional deadline for the task. Defaults to None.
        """
        self.__description = description
        self.__priority = priority
        self.__deadline = deadline

    @property
    def description(self) -> str:
        """Description of the task that needs handover."""
        return self.__description

    @property
    def priority(self) -> str:
        """Priority level of the task."""
        return self.__priority

    @property
    def deadline(self) -> str | None:
        """Optional deadline for the task."""
        return self.__deadline


class KnowledgeArea:
    """Immutable value object representing a critical knowledge area."""

    def __init__(self, topic: str, description: str, expertise_level: str) -> None:
        """Initialize the knowledge area value object.

        Args:
            topic: The knowledge domain or subject area.
            description: Description of the knowledge and its importance.
            expertise_level: The departing employee's level of expertise in this area.
        """
        self.__topic = topic
        self.__description = description
        self.__expertise_level = expertise_level

    @property
    def topic(self) -> str:
        """The knowledge domain or subject area."""
        return self.__topic

    @property
    def description(self) -> str:
        """Description of the knowledge and its importance."""
        return self.__description

    @property
    def expertise_level(self) -> str:
        """The departing employee's level of expertise in this area."""
        return self.__expertise_level


class DossierSection(ABC):
    """Abstract base class for a dossier section."""

    def __init__(self, title: str) -> None:
        """Initialize the section with its title.

        Args:
            title: Human-readable title of the section.
        """
        self.__title = title

    @property
    def title(self) -> str:
        """Human-readable title of the section."""
        return self.__title

    @abstractmethod
    def get_section_type(self) -> str:
        """Returns a discriminator string identifying the section type."""


class ResponsibilitiesSection(DossierSection):
    """Key responsibilities the departing employee held."""

    def __init__(self, title: str, responsibilities: list[str]) -> None:
        """Initialize the responsibilities section.

        Args:
            title: Human-readable title of the section.
            responsibilities: List of responsibility descriptions.
        """
        super().__init__(title)
        self.__responsibilities = responsibilities

    @property
    def responsibilities(self) -> list[str]:
        """A copy of the list of responsibility descriptions."""
        return list(self.__responsibilities)

    def get_section_type(self) -> str:
        """Returns the section type discriminator: 'responsibilities'."""
        return "responsibilities"


class ContactsSection(DossierSection):
    """Key internal/external contacts the successor should know."""

    def __init__(self, title: str, contacts: list[Contact]) -> None:
        """Initialize the contacts section.

        Args:
            title: Human-readable title of the section.
            contacts: List of key contacts to transfer knowledge about.
        """
        super().__init__(title)
        self.__contacts = contacts

    @property
    def contacts(self) -> list[Contact]:
        """A copy of the list of key contacts."""
        return list(self.__contacts)

    def get_section_type(self) -> str:
        """Returns the section type discriminator: 'contacts'."""
        return "contacts"


class PendingTasksSection(DossierSection):
    """Tasks still open or in-progress that need handover."""

    def __init__(self, title: str, tasks: list[PendingTask]) -> None:
        """Initialize the pending tasks section.

        Args:
            title: Human-readable title of the section.
            tasks: List of pending tasks that need handover.
        """
        super().__init__(title)
        self.__tasks = tasks

    @property
    def tasks(self) -> list[PendingTask]:
        """A copy of the list of pending tasks."""
        return list(self.__tasks)

    def get_section_type(self) -> str:
        """Returns the section type discriminator: 'pending_tasks'."""
        return "pending_tasks"


class KnowledgeAreasSection(DossierSection):
    """Critical knowledge areas and documentation pointers."""

    def __init__(self, title: str, areas: list[KnowledgeArea]) -> None:
        """Initialize the knowledge areas section.

        Args:
            title: Human-readable title of the section.
            areas: List of critical knowledge areas to document.
        """
        super().__init__(title)
        self.__areas = areas

    @property
    def areas(self) -> list[KnowledgeArea]:
        """A copy of the list of knowledge areas."""
        return list(self.__areas)

    def get_section_type(self) -> str:
        """Returns the section type discriminator: 'knowledge_areas'."""
        return "knowledge_areas"
