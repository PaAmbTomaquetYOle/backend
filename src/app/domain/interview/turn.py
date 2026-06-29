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
        self.__speaker_role = speaker_role
        self.__timestamp = timestamp
        self.__content = content
        self.__order = order
        self.__topic = topic
        self.__sentiment = sentiment

    @property
    def speaker_role(self) -> SpeakerRoleEnum:
        return self.__speaker_role

    @property
    def timestamp(self) -> datetime:
        return self.__timestamp

    @property
    def content(self) -> str:
        return self.__content

    @property
    def order(self) -> int:
        return self.__order

    @property
    def topic(self) -> str | None:
        return self.__topic

    @property
    def sentiment(self) -> str | None:
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
        super().__init__(speaker_role, timestamp, content, order, topic, sentiment)
        self.__answer_text = answer_text

    @property
    def answer_text(self) -> str | None:
        return self.__answer_text

    @answer_text.setter
    def answer_text(self, value: str | None) -> None:
        self.__answer_text = value

    def get_turn_type(self) -> str:
        return "question"


class InterviewNote(InterviewTurn):
    """A free-form note turn."""

    def get_turn_type(self) -> str:
        return "note"
