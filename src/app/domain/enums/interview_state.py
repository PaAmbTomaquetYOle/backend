"""Enum of valid interview states."""

from enum import Enum


class InterviewStateEnum(Enum):
    """Enumeration of possible interview lifecycle states."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
