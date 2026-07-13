"""Composition helpers shared by the FastAPI DI layer and the Kafka consumer.

FastAPI routers assemble use cases via ``Depends`` (see
``infrastructure/api/dependencies.py``), which works because a request has a
request-scoped session available through the dependency graph. The Kafka
consumer processes messages outside of any HTTP request, so it cannot use
``Depends`` — it needs to build the exact same object graph by hand, once per
message, with its own session. This module is the single place that knows how
to assemble an ``OffboardingFacadeService``, so both call sites stay in sync.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.dossier_generator import IDossierGenerator
from app.application.ports.event_publisher import IEventPublisher
from app.application.ports.graph_database import IGraphDatabasePort
from app.application.ports.metrics import IMetricsPort
from app.application.services.annual_review_facade_service import AnnualReviewFacadeService
from app.application.services.annual_review_process_service import AnnualReviewProcessService
from app.application.services.dossier_service import DossierService
from app.application.services.inbound_context import InboundContext
from app.application.services.interview_service import InterviewService
from app.application.services.knowledge_graph_service import KnowledgeGraphService
from app.application.services.monthly_review_facade_service import MonthlyReviewFacadeService
from app.application.services.monthly_review_process_service import MonthlyReviewProcessService
from app.application.services.offboarding_facade_service import OffboardingFacadeService
from app.application.services.offboarding_process_service import OffboardingProcessService
from app.application.services.offboarding_task_service import OffboardingTaskService
from app.application.services.review_scheduling_service import ReviewSchedulingService
from app.application.services.sop_candidate_service import SopCandidateService
from app.application.services.sop_service import SopService
from app.infrastructure.adapters.graph.knowledge_graph_repository import (
    Neo4jKnowledgeGraphRepository,
)
from app.infrastructure.adapters.repositories.annual_review_process import (
    AnnualReviewProcessRepository,
)
from app.infrastructure.adapters.repositories.dossier import DossierRepository
from app.infrastructure.adapters.repositories.interview import InterviewRepository
from app.infrastructure.adapters.repositories.monthly_review_process import (
    MonthlyReviewProcessRepository,
)
from app.infrastructure.adapters.repositories.offboarding_process import (
    OffboardingProcessRepository,
)
from app.infrastructure.adapters.repositories.offboarding_task import OffboardingTaskRepository
from app.infrastructure.adapters.repositories.sop import SopRepository
from app.infrastructure.adapters.repositories.sop_candidate import SopCandidateRepository


def build_offboarding_facade(
    session: AsyncSession,
    event_publisher: IEventPublisher | None = None,
    dossier_generator: IDossierGenerator | None = None,
    metrics: IMetricsPort | None = None,
) -> OffboardingFacadeService:
    """Assemble a fully wired OffboardingFacadeService from a session.

    Args:
        session: The active SQLModel session shared across the composed services.
        event_publisher: Optional event publisher for domain event dispatching.
        dossier_generator: Optional generator used by generate_dossier.
        metrics: Optional port for recording a failed event publish (BE-20).

    Returns:
        OffboardingFacadeService: A fully wired facade instance.
    """
    return OffboardingFacadeService(
        process_service=OffboardingProcessService(OffboardingProcessRepository(session)),
        interview_service=InterviewService(InterviewRepository(session)),
        dossier_service=DossierService(DossierRepository(session)),
        event_publisher=event_publisher,
        dossier_generator=dossier_generator,
        metrics=metrics,
    )


def build_monthly_review_facade(
    session: AsyncSession,
    event_publisher: IEventPublisher | None = None,
    dossier_generator: IDossierGenerator | None = None,
    metrics: IMetricsPort | None = None,
) -> MonthlyReviewFacadeService:
    """Assemble a fully wired MonthlyReviewFacadeService from a session.

    Args:
        session: The active SQLModel session shared across the composed services.
        event_publisher: Optional event publisher for domain event dispatching.
        dossier_generator: Optional generator used by generate_dossier.
        metrics: Optional port for recording a failed event publish (BE-20).

    Returns:
        MonthlyReviewFacadeService: A fully wired facade instance.
    """
    return MonthlyReviewFacadeService(
        process_service=MonthlyReviewProcessService(MonthlyReviewProcessRepository(session)),
        interview_service=InterviewService(InterviewRepository(session)),
        dossier_service=DossierService(DossierRepository(session)),
        event_publisher=event_publisher,
        dossier_generator=dossier_generator,
        metrics=metrics,
    )


def build_annual_review_facade(
    session: AsyncSession,
    event_publisher: IEventPublisher | None = None,
    dossier_generator: IDossierGenerator | None = None,
    metrics: IMetricsPort | None = None,
) -> AnnualReviewFacadeService:
    """Assemble a fully wired AnnualReviewFacadeService from a session.

    Args:
        session: The active SQLModel session shared across the composed services.
        event_publisher: Optional event publisher for domain event dispatching.
        dossier_generator: Optional generator used by generate_dossier.
        metrics: Optional port for recording a failed event publish (BE-20).

    Returns:
        AnnualReviewFacadeService: A fully wired facade instance.
    """
    return AnnualReviewFacadeService(
        process_service=AnnualReviewProcessService(AnnualReviewProcessRepository(session)),
        interview_service=InterviewService(InterviewRepository(session)),
        dossier_service=DossierService(DossierRepository(session)),
        event_publisher=event_publisher,
        dossier_generator=dossier_generator,
        metrics=metrics,
    )


def build_review_scheduling_service(
    session: AsyncSession,
    event_publisher: IEventPublisher | None = None,
    dossier_generator: IDossierGenerator | None = None,
    metrics: IMetricsPort | None = None,
) -> ReviewSchedulingService:
    """Assemble a fully wired ReviewSchedulingService from a session (BE-24).

    Args:
        session: The active SQLModel session shared across the composed services.
        event_publisher: Optional event publisher for domain event dispatching.
        dossier_generator: Optional generator used by generate_dossier.
        metrics: Optional port for recording a failed event publish (BE-20).

    Returns:
        ReviewSchedulingService: A fully wired scheduling service instance.
    """
    return ReviewSchedulingService(
        offboarding_facade=build_offboarding_facade(
            session, event_publisher, dossier_generator, metrics
        ),
        monthly_review_facade=build_monthly_review_facade(
            session, event_publisher, dossier_generator, metrics
        ),
        annual_review_facade=build_annual_review_facade(
            session, event_publisher, dossier_generator, metrics
        ),
    )


def build_sop_service(
    session: AsyncSession,
    event_publisher: IEventPublisher | None = None,
    dialect_name: str = "postgresql",
    metrics: IMetricsPort | None = None,
) -> SopService:
    """Assemble a fully wired SopService from a session.

    Args:
        session: The active SQLModel session used by the SOP repository.
        event_publisher: Optional event publisher used to publish SOPCreated.
        dialect_name: The SQL dialect in use, forwarded to SopRepository to
            pick its text search strategy. Defaults to "postgresql".
        metrics: Optional port for recording a failed event publish (BE-20).

    Returns:
        SopService: A fully wired SOP service instance.
    """
    return SopService(
        SopRepository(session, dialect_name=dialect_name),
        event_publisher=event_publisher,
        metrics=metrics,
    )


def build_sop_candidate_service(session: AsyncSession) -> SopCandidateService:
    """Assemble a fully wired SopCandidateService from a session.

    Args:
        session: The active SQLModel session used by the SOP candidate repository.

    Returns:
        SopCandidateService: A fully wired SOP candidate service instance.
    """
    return SopCandidateService(SopCandidateRepository(session))


def build_task_service(session: AsyncSession) -> OffboardingTaskService:
    """Assemble a fully wired OffboardingTaskService from a session.

    Args:
        session: The active SQLModel session used by the offboarding task repository.

    Returns:
        OffboardingTaskService: A fully wired offboarding task service instance.
    """
    return OffboardingTaskService(OffboardingTaskRepository(session))


def build_knowledge_graph_service(
    graph_db: IGraphDatabasePort,
    event_publisher: IEventPublisher | None = None,
    metrics: IMetricsPort | None = None,
) -> KnowledgeGraphService:
    """Assemble a fully wired KnowledgeGraphService from a graph database port.

    Args:
        graph_db: The graph database port used by the Neo4j-backed repository.
        event_publisher: Optional event publisher used to publish KnowledgeGraphUpdated.
        metrics: Optional port for recording a failed event publish (BE-20).

    Returns:
        KnowledgeGraphService: A fully wired knowledge graph service instance.
    """
    return KnowledgeGraphService(
        Neo4jKnowledgeGraphRepository(graph_db), event_publisher=event_publisher, metrics=metrics
    )


def build_inbound_context(
    session: AsyncSession,
    graph_db: IGraphDatabasePort,
    event_publisher: IEventPublisher | None = None,
    dossier_generator: IDossierGenerator | None = None,
    metrics: IMetricsPort | None = None,
) -> InboundContext:
    """Assemble the per-message InboundContext used by the Kafka consumer.

    Bundles every bounded-context service an inbound event handler might
    need, built fresh per message from a single session (mirroring how
    FastAPI's Depends builds a per-request facade).

    Args:
        session: The active SQLModel session shared across the composed services.
        graph_db: The graph database port used by the knowledge graph service.
        event_publisher: Optional event publisher for domain event dispatching.
        dossier_generator: Optional generator used by generate_dossier.
        metrics: Optional port for recording a failed event publish (BE-20).

    Returns:
        InboundContext: The composed per-message context.
    """
    dialect_name = session.get_bind().dialect.name
    return InboundContext(
        offboarding=build_offboarding_facade(
            session, event_publisher, dossier_generator, metrics
        ),
        monthly_review=build_monthly_review_facade(
            session, event_publisher, dossier_generator, metrics
        ),
        annual_review=build_annual_review_facade(
            session, event_publisher, dossier_generator, metrics
        ),
        sops=build_sop_service(
            session, event_publisher, dialect_name=dialect_name, metrics=metrics
        ),
        sop_candidates=build_sop_candidate_service(session),
        tasks=build_task_service(session),
        knowledge_graph=build_knowledge_graph_service(graph_db, event_publisher, metrics),
    )
