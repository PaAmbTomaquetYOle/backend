"""Read-only HTTP endpoint for SOP candidates (SA-16).

Candidates are Kafka-only for writes ('sop.candidate_offered' /
'sop.candidate_decided', matching the offboarding write-convergence policy) —
see `domain/events/inbound_events.py`. This endpoint exists so slack-agent
can rehydrate its pending-candidate cache after a restart.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.service_interfaces.sop_candidate_service_interface import (
    ISopCandidateService,
)
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.api.dependencies import sop_candidate_service_dependency
from app.infrastructure.api.schemas.sop_candidate import (
    SopCandidateListResponse,
    sop_candidate_to_response,
)

router = APIRouter(
    prefix="/sop-candidates",
    tags=["sop-candidates"],
    dependencies=[Depends(get_current_service)],
)


@router.get(
    "",
    response_model=SopCandidateListResponse,
    summary="List SOP candidates still awaiting a decision",
)
async def list_pending_sop_candidates(
        service: Annotated[ISopCandidateService, Depends(sop_candidate_service_dependency)],
) -> SopCandidateListResponse:
    """Return every candidate still awaiting a decision, for rehydration."""
    candidates = await service.list_pending()
    return SopCandidateListResponse(items=[sop_candidate_to_response(c) for c in candidates])
