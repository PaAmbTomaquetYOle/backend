from app.domain.exceptions.base import DomainException


class InterviewDomainError(DomainException):
    """Base exception for Interview domain errors."""
    def __init__(self, message: str):
        super().__init__(message)


class InterviewAlreadyExistsForProcessError(InterviewDomainError):
    """Raised when trying to create a second interview for a process (1:1 constraint)."""
    def __init__(self, process_id_str: str):
        super().__init__(f"An interview already exists for process {process_id_str}")


class InterviewTurnOrderError(InterviewDomainError):
    """Raised when an invalid turn order is provided."""
    def __init__(self, message: str):
        super().__init__(message)


class InterviewNotInProgressError(InterviewDomainError):
    """Raised when trying to add turns to an interview that is not in progress."""
    def __init__(self):
        super().__init__("Cannot add turns: interview is not in progress")
