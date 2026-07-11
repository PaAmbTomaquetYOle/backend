"""Enum of valid annual review process states."""

from app.domain.enums.process_state import ProcessStateEnum


class AnnualReviewProcessStateEnum(ProcessStateEnum):
    """
    Enum representing the different states of the annual review process.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVISION = "pending_revision"
    FINISHED = "finished"
    CANCELLED = "cancelled"
