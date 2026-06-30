"""Concrete SQLModel-backed repository implementations.

Each class implements its corresponding port interface from application.ports.
"""

from app.infrastructure.adapters.repositories.dossier import (
    DossierRepository as DossierRepository,
)
from app.infrastructure.adapters.repositories.interview import (
    InterviewRepository as InterviewRepository,
)
from app.infrastructure.adapters.repositories.offboarding_process import (
    OffboardingProcessRepository as OffboardingProcessRepository,
)
