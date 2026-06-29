from app.domain.exceptions.base import DomainException


class DossierDomainError(DomainException):
    """Base exception for Dossier domain errors."""
    def __init__(self, message: str):
        super().__init__(message)


class DossierInterviewNotCompletedError(DossierDomainError):
    """Raised when trying to generate a dossier before the interview is completed."""
    def __init__(self):
        super().__init__("Cannot generate dossier: interview is not completed")


class DossierAlreadyExistsForProcessError(DossierDomainError):
    """Raised when trying to create a second dossier for a process."""
    def __init__(self, process_id_str: str):
        super().__init__(f"A dossier already exists for process {process_id_str}")


class DossierSectionError(DossierDomainError):
    """Raised for section-related validation errors."""
    def __init__(self, message: str):
        super().__init__(message)
