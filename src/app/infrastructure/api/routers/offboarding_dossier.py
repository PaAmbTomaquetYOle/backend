"""HTTP endpoints for dossier management within an offboarding process.

Dossier creation happens exclusively via the Kafka
``dossier.generation_requested`` command — see
``domain/events/inbound_events.py`` — this router is read-only.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingDossierFacade,
)
from app.domain import OffboardingProcessId
from app.infrastructure.api.dependencies import offboarding_dossier_facade_dependency
from app.infrastructure.api.schemas.common import ErrorResponse
from app.infrastructure.api.schemas.dossier import DossierResponse, dossier_to_response

router = APIRouter(tags=["dossier"])

_404 = {
    404:
        {
            "model": ErrorResponse,
            "description": "Process or dossier not found"
        }
}


@router.get(
    "/{process_id}/dossier",
    response_model=DossierResponse,
    status_code=status.HTTP_200_OK,
    responses=_404,
    summary="Get dossier for an offboarding process",
)
async def get_dossier(
        process_id: UUID,
        facade: Annotated[
            IOffboardingDossierFacade,
            Depends(offboarding_dossier_facade_dependency)
        ],
) -> DossierResponse:
    """Retrieve the dossier for an offboarding process."""
    dossier = await facade.get_dossier(OffboardingProcessId(process_id))
    return dossier_to_response(dossier)
