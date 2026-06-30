from app.domain.exceptions.base import DomainException


class OffboardingDomainError(DomainException):
    def __init__(self, message: str):
        super().__init__(message)


class ProcessNotFoundError(OffboardingDomainError):
    def __init__(self, process_id_str: str):
        super().__init__(f"Offboarding process {process_id_str} not found")
