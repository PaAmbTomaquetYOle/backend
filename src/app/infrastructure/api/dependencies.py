"""FastAPI dependency wiring (composition of ports and adapters).

This module is the place to assemble use cases with their concrete adapters and
expose them as FastAPI dependencies via ``Depends``. It will grow as bounded
contexts (Slack, LLM agent, ...) are added.
"""

from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingFacadeService,
)
from app.application.services.dossier_service import DossierService
from app.application.services.interview_service import InterviewService
from app.application.services.offboarding_facade_service import OffboardingFacadeService
from app.application.services.offboarding_process_service import OffboardingProcessService
from app.infrastructure.adapters.repositories.dossier import DossierRepository
from app.infrastructure.adapters.repositories.interview import InterviewRepository
from app.infrastructure.adapters.repositories.offboarding_process import (
    OffboardingProcessRepository,
)
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.persistence.database import get_session


def settings_dependency() -> Settings:
    """Expose application settings as a FastAPI dependency."""
    return get_settings()


def offboarding_repository_dependency(
    session: Annotated[Session, Depends(get_session)],
) -> OffboardingProcessRepository:
    """Provide a SQLModel-backed offboarding process repository."""
    return OffboardingProcessRepository(session)


def interview_repository_dependency(
    session: Annotated[Session, Depends(get_session)],
) -> InterviewRepository:
    return InterviewRepository(session)


def dossier_repository_dependency(
    session: Annotated[Session, Depends(get_session)],
) -> DossierRepository:
    return DossierRepository(session)


def offboarding_process_service_dependency(
    session: Annotated[Session, Depends(get_session)],
) -> OffboardingProcessService:
    return OffboardingProcessService(OffboardingProcessRepository(session))


def interview_service_dependency(
    session: Annotated[Session, Depends(get_session)],
) -> InterviewService:
    return InterviewService(InterviewRepository(session))


def dossier_service_dependency(
    session: Annotated[Session, Depends(get_session)],
) -> DossierService:
    return DossierService(DossierRepository(session))


def offboarding_facade_dependency(
    session: Annotated[Session, Depends(get_session)],
) -> IOffboardingFacadeService:
    return OffboardingFacadeService(
        process_service=OffboardingProcessService(OffboardingProcessRepository(session)),
        interview_service=InterviewService(InterviewRepository(session)),
        dossier_service=DossierService(DossierRepository(session)),
    )
