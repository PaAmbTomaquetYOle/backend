from app.domain.enums.process_state import ProcessStateEnum


class OffboardingProcessStateEnum(ProcessStateEnum):
    """
    Enum representing the different states of the offboarding process.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVISION = "pending_revision"
    FINISHED = "finished"
    CANCELLED = "cancelled"
