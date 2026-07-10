"""Exceptions raised by the knowledge graph domain."""

from app.domain.exceptions.base import DomainException


class KnowledgeGraphDomainError(DomainException):
    """Base exception for knowledge graph domain errors."""

    def __init__(self, message: str):
        """Initialize with an error message.

        Args:
            message: Human-readable description of the error.
        """
        super().__init__(message)


class PersonNotFoundInGraphError(KnowledgeGraphDomainError):
    """Raised when a person with the given ID does not exist in the graph."""

    def __init__(self, person_id: str):
        """Initialize with the ID of the missing person.

        Args:
            person_id: External Slack user ID that was not found in the graph.
        """
        super().__init__(f"Person {person_id} not found in knowledge graph")


class TopicNotFoundInGraphError(KnowledgeGraphDomainError):
    """Raised when a topic with the given name does not exist in the graph."""

    def __init__(self, topic_name: str):
        """Initialize with the name of the missing topic.

        Args:
            topic_name: Topic name that was not found in the graph.
        """
        super().__init__(f"Topic '{topic_name}' not found in knowledge graph")
