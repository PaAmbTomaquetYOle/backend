"""FastAPI dependency wiring (composition of ports and adapters).

This module is the place to assemble use cases with their concrete adapters and
expose them as FastAPI dependencies via ``Depends``. It will grow as bounded
contexts (Slack, LLM agent, ...) are added.
"""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.event_publisher import IEventPublisher
from app.application.ports.graph_database import IGraphDatabasePort
from app.application.ports.service_credential_repository import IServiceCredentialRepository
from app.application.ports.token_issuer import ITokenIssuer
from app.application.service_interfaces.knowledge_graph_service_interface import (
    IKnowledgeGraphService,
)
from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingDossierFacade,
    IOffboardingInterviewFacade,
    IOffboardingProcessFacade,
)
from app.application.service_interfaces.sop_service_interface import ISopService
from app.application.services.dossier_service import DossierService
from app.application.services.interview_service import InterviewService
from app.application.services.offboarding_process_service import OffboardingProcessService
from app.application.services.token_service import TokenService
from app.infrastructure.adapters.auth.env_service_credential_repository import (
    EnvServiceCredentialRepository,
)
from app.infrastructure.adapters.auth.jwt_token_issuer import JwtTokenIssuer
from app.infrastructure.adapters.repositories.dossier import DossierRepository
from app.infrastructure.adapters.repositories.interview import InterviewRepository
from app.infrastructure.adapters.repositories.offboarding_process import (
    OffboardingProcessRepository,
)
from app.infrastructure.composition import (
    build_knowledge_graph_service,
    build_offboarding_facade,
    build_sop_service,
)
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.persistence.database import get_session


def settings_dependency() -> Settings:
    """Expose application settings as a FastAPI dependency."""
    return get_settings()


def graph_database_dependency(request: Request) -> IGraphDatabasePort:
    """Retrieve the graph database port from application state."""
    return request.app.state.graph_db


def offboarding_repository_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OffboardingProcessRepository:
    """Provide a SQLModel-backed offboarding process repository."""
    return OffboardingProcessRepository(session)


def interview_repository_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InterviewRepository:
    """Provide a SQLModel-backed interview repository."""
    return InterviewRepository(session)


def dossier_repository_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DossierRepository:
    """Provide a SQLModel-backed dossier repository."""
    return DossierRepository(session)


def offboarding_process_service_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OffboardingProcessService:
    """Provide an offboarding process service wired with its repository."""
    return OffboardingProcessService(OffboardingProcessRepository(session))


def interview_service_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InterviewService:
    """Provide an interview service wired with its repository."""
    return InterviewService(InterviewRepository(session))


def dossier_service_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DossierService:
    """Provide a dossier service wired with its repository."""
    return DossierService(DossierRepository(session))


def event_publisher_dependency(request: Request) -> IEventPublisher:
    """Retrieve the event publisher from application state."""
    return request.app.state.event_publisher


def offboarding_process_facade_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> IOffboardingProcessFacade:
    """Provide the facade narrowed to IOffboardingProcessFacade for the process router."""
    publisher = getattr(request.app.state, "event_publisher", None)
    return build_offboarding_facade(session, publisher)


def offboarding_interview_facade_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> IOffboardingInterviewFacade:
    """Provide the facade narrowed to IOffboardingInterviewFacade for the interview router."""
    publisher = getattr(request.app.state, "event_publisher", None)
    return build_offboarding_facade(session, publisher)


def offboarding_dossier_facade_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> IOffboardingDossierFacade:
    """Provide the facade narrowed to IOffboardingDossierFacade for the dossier router."""
    publisher = getattr(request.app.state, "event_publisher", None)
    generator = getattr(request.app.state, "dossier_generator", None)
    return build_offboarding_facade(session, publisher, generator)


def sop_service_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> ISopService:
    """Provide a SOP service wired with its repository and the event publisher."""
    publisher = getattr(request.app.state, "event_publisher", None)
    return build_sop_service(session, publisher)


def knowledge_graph_service_dependency(request: Request) -> IKnowledgeGraphService:
    """Provide a knowledge graph service wired with its Neo4j-backed repository."""
    graph_db = request.app.state.graph_db
    publisher = getattr(request.app.state, "event_publisher", None)
    return build_knowledge_graph_service(graph_db, publisher)


def service_credential_repository_dependency(
    settings: Annotated[Settings, Depends(get_settings)],
) -> IServiceCredentialRepository:
    """Provide the env-backed service credential repository."""
    return EnvServiceCredentialRepository(settings)


def token_issuer_dependency(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ITokenIssuer:
    """Provide the JWT-based token issuer."""
    return JwtTokenIssuer(settings)


def token_service_dependency(
    credential_repository: Annotated[
        IServiceCredentialRepository, Depends(service_credential_repository_dependency)
    ],
    token_issuer: Annotated[ITokenIssuer, Depends(token_issuer_dependency)],
) -> TokenService:
    """Provide the token service wired with its credential repository and issuer."""
    return TokenService(credential_repository, token_issuer)
