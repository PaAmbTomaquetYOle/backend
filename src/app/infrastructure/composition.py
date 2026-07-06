"""Composition helpers shared by the FastAPI DI layer and the Kafka consumer.

FastAPI routers assemble use cases via ``Depends`` (see
``infrastructure/api/dependencies.py``), which works because a request has a
request-scoped session available through the dependency graph. The Kafka
consumer processes messages outside of any HTTP request, so it cannot use
``Depends`` — it needs to build the exact same object graph by hand, once per
message, with its own session. This module is the single place that knows how
to assemble an ``OffboardingFacadeService``, so both call sites stay in sync.
"""

from sqlmodel import Session

from app.application.ports.dossier_generator import IDossierGenerator
from app.application.ports.event_publisher import IEventPublisher
from app.application.services.dossier_service import DossierService
from app.application.services.interview_service import InterviewService
from app.application.services.offboarding_facade_service import OffboardingFacadeService
from app.application.services.offboarding_process_service import OffboardingProcessService
from app.infrastructure.adapters.repositories.dossier import DossierRepository
from app.infrastructure.adapters.repositories.interview import InterviewRepository
from app.infrastructure.adapters.repositories.offboarding_process import (
    OffboardingProcessRepository,
)


def build_offboarding_facade(
    session: Session,
    event_publisher: IEventPublisher | None = None,
    dossier_generator: IDossierGenerator | None = None,
) -> OffboardingFacadeService:
    """Assemble a fully wired OffboardingFacadeService from a session.

    Args:
        session: The active SQLModel session shared across the composed services.
        event_publisher: Optional event publisher for domain event dispatching.
        dossier_generator: Optional generator used by generate_dossier.

    Returns:
        OffboardingFacadeService: A fully wired facade instance.
    """
    return OffboardingFacadeService(
        process_service=OffboardingProcessService(OffboardingProcessRepository(session)),
        interview_service=InterviewService(InterviewRepository(session)),
        dossier_service=DossierService(DossierRepository(session)),
        event_publisher=event_publisher,
        dossier_generator=dossier_generator,
    )
