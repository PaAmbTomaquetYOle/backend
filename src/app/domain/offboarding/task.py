"""OffboardingTask aggregate root — a pending Jira/Trello task belonging to a departing
employee, extracted via MCP during the guided interview (SA-18).

Like SopCandidate, this has no branching lifecycle state machine — it is a flat, replaceable
snapshot: whenever slack-agent (re-)extracts tasks for a process, the full set for that process
is persisted and replaces whatever was stored before, so it is modeled as a plain value-bearing
aggregate rather than a state/ subpackage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.enums import TaskSourceEnum

if TYPE_CHECKING:
    from app.domain.offboarding.id import OffboardingProcessId


class OffboardingTask:
    """A single pending Jira/Trello task extracted for a departing employee.

    Identity is the external (task_id, source) pair scoped to a process — task_id is owned by
    the external collaboration tool (a Jira issue key or a Trello card id), not generated here.
    """

    __process_id: OffboardingProcessId
    __task_id: str
    __title: str
    __source: TaskSourceEnum
    __status: str
    __url: str | None
    __description: str | None

    def __init__(
            self,
            process_id: OffboardingProcessId,
            task_id: str,
            title: str,
            source: TaskSourceEnum,
            status: str,
            url: str | None = None,
            description: str | None = None,
    ) -> None:
        """Initialize the task with all its attributes.

        Args:
            process_id: The offboarding process this task belongs to.
            task_id: The external Jira issue key or Trello card id.
            title: Title of the task.
            source: Which collaboration tool the task was extracted from.
            status: Current status of the task in its collaboration tool.
            url: Link to the task in the external tool, if known. Defaults to None.
            description: Detailed description of the task, if known. Defaults to None.
        """
        self.__process_id = process_id
        self.__task_id = task_id
        self.__title = title
        self.__source = source
        self.__status = status
        self.__url = url
        self.__description = description

    @property
    def process_id(self) -> OffboardingProcessId:
        """The offboarding process this task belongs to."""
        return self.__process_id

    @property
    def task_id(self) -> str:
        """The external Jira issue key or Trello card id."""
        return self.__task_id

    @property
    def title(self) -> str:
        """Title of the task."""
        return self.__title

    @property
    def source(self) -> TaskSourceEnum:
        """Which collaboration tool the task was extracted from."""
        return self.__source

    @property
    def status(self) -> str:
        """Current status of the task in its collaboration tool."""
        return self.__status

    @property
    def url(self) -> str | None:
        """Link to the task in the external tool, if known."""
        return self.__url

    @property
    def description(self) -> str | None:
        """Detailed description of the task, if known."""
        return self.__description
