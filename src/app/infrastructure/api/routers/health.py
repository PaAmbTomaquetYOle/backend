"""Health check endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.graph_database import IGraphDatabasePort
from app.infrastructure.adapters.events.kafka_event_publisher import KafkaEventPublisher
from app.infrastructure.api.dependencies import get_session, graph_database_dependency

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return a simple liveness status."""
    return {"status": "ok"}


@router.get("/health/db")
async def health_db(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    graph_db: Annotated[IGraphDatabasePort, Depends(graph_database_dependency)],
) -> JSONResponse:
    """Return readiness status by checking database connections."""
    postgres_ok = False
    try:
        await session.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception:
        pass

    neo4j_ok = await graph_db.verify_connectivity()

    event_publisher = getattr(request.app.state, "event_publisher", None)
    kafka_ok = isinstance(event_publisher, KafkaEventPublisher)

    db_status = {
        "postgres": "ok" if postgres_ok else "error",
        "neo4j": "ok" if neo4j_ok else "error",
        "kafka": "ok" if kafka_ok else "error",
    }

    if not postgres_ok or not neo4j_ok or not kafka_ok:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=db_status)

    return JSONResponse(status_code=status.HTTP_200_OK, content=db_status)

