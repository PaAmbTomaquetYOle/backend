"""Origin collaboration tool of an extracted offboarding task (SA-18)."""

from enum import Enum


class TaskSourceEnum(str, Enum):
    """Which collaboration tool a pending task was extracted from."""

    JIRA = "jira"
    TRELLO = "trello"
