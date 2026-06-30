"""Interview turn value objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.enums import SpeakerRoleEnum


class InterviewTurn(ABC):
    """Abstract base class for a single turn within an interview conversation."""

    def __init__(
        self,
        speaker_role: SpeakerRoleEnum,
        timestamp: datetime,
        content: str,
        order: int,
        topic: str | None = None,
        sentiment: str | None = None,
    ) -> None:
        """Initialize a conversation turn.

        Args:
            speaker_role: The role of the speaker (interviewer or interviewee).
            timestamp: When this turn occurred.
            content: The text content of the turn.
            order: Zero-based position of this turn in the conversation sequence.
            topic: Optional topic tag for the turn. Defaults to None.
            sentiment: Optional sentiment label for the turn. Defaults to None.
        """
        self.__speaker_role = speaker_role
        self.__timestamp = timestamp
        self.__content = content
        self.__order = order
        self.__topic = topic
        self.__sentiment = sentiment

    @property
    def speaker_role(self) -> SpeakerRoleEnum:
        """The role of the speaker who produced this turn."""
        return self.__speaker_role

    @property
    def timestamp(self) -> datetime:
        """When this turn occurred."""
        return self.__timestamp

    @property
    def content(self) -> str:
        """The text content of this turn."""
        return self.__content

    @property
    def order(self) -> int:
        """Zero-based position of this turn in the conversation sequence."""
        return self.__order

    @property
    def topic(self) -> str | None:
        """Optional topic tag for this turn."""
        return self.__topic

    @property
    def sentiment(self) -> str | None:
        """Optional sentiment label for this turn."""
        return self.__sentiment

    @abstractmethod
    def get_turn_type(self) -> str:
        """Returns a discriminator string identifying the turn type."""


class InterviewQuestion(InterviewTurn):
    """A structured question turn, optionally with an answer."""

    def __init__(
        self,
        speaker_role: SpeakerRoleEnum,
        timestamp: datetime,
        content: str,
        order: int,
        topic: str | None = None,
        sentiment: str | None = None,
        answer_text: str | None = None,
    ) -> None:
        """Initialize a question turn.

        Args:
            speaker_role: The role of the speaker asking the question.
            timestamp: When this turn occurred.
            content: The question text.
            order: Zero-based position of this turn in the conversation sequence.
            topic: Optional topic tag. Defaults to None.
            sentiment: Optional sentiment label. Defaults to None.
            answer_text: Optional answer to the question. Defaults to None.
        """
        super().__init__(speaker_role, timestamp, content, order, topic, sentiment)
        self.__answer_text = answer_text

    @property
    def answer_text(self) -> str | None:
        """The answer text for this question turn, if any."""
        return self.__answer_text

    @answer_text.setter
    def answer_text(self, value: str | None) -> None:
        """Set or update the answer text."""
        self.__answer_text = value

    def get_turn_type(self) -> str:
        """Returns the turn type discriminator: 'question'."""
        return "question"


class InterviewNote(InterviewTurn):
    """A free-form note turn."""

    def get_turn_type(self) -> str:
        """Returns the turn type discriminator: 'note'."""
        return "note"
