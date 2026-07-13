"""Enum of valid monthly review process states."""

from app.domain.enums.process_state import ProcessStateEnum


class MonthlyReviewProcessStateEnum(ProcessStateEnum):
    """
    Enum representing the different states of the monthly review process.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"
