from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.service_interfaces.offboarding_facade_interface import IOffboardingDossierFacade
from app.domain import DossierSection, OffboardingProcessId
from app.infrastructure.api.dependencies import offboarding_dossier_facade_dependency
from app.infrastructure.api.schemas.common import ErrorResponse
from app.infrastructure.api.schemas.dossier import (
    CreateDossierRequest,
    DossierResponse,
    dossier_to_response,
)

router = APIRouter(tags=["dossier"])

_404 = {404: {"model": ErrorResponse, "description": "Process or dossier not found"}}
_409 = {409: {"model": ErrorResponse, "description": "Dossier already exists or constraint violation"}}
_422 = {422: {"model": ErrorResponse, "description": "Interview not completed"}}


@router.post(
    "/{process_id}/dossier",
    response_model=DossierResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**_404, **_409, **_422},
    summary="Create dossier for an offboarding process",
)
async def create_dossier(
        process_id: UUID,
        body: CreateDossierRequest,
        facade: Annotated[IOffboardingDossierFacade, Depends(offboarding_dossier_facade_dependency)],
) -> DossierResponse:
    pid = OffboardingProcessId(process_id)
    sections: list[DossierSection] = [s.to_domain() for s in body.sections]
    dossier = await facade.create_dossier(
        process_id=pid,
        summary=body.summary,
        sections=sections or None,
    )
    return dossier_to_response(dossier)


@router.get(
    "/{process_id}/dossier",
    response_model=DossierResponse,
    status_code=status.HTTP_200_OK,
    responses=_404,
    summary="Get dossier for an offboarding process",
)
async def get_dossier(
        process_id: UUID,
        facade: Annotated[IOffboardingDossierFacade, Depends(offboarding_dossier_facade_dependency)],
) -> DossierResponse:
    dossier = await facade.get_dossier(OffboardingProcessId(process_id))
    return dossier_to_response(dossier)
