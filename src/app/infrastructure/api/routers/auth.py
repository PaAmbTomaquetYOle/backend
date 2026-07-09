"""HTTP endpoint for the client-credentials token grant.

Unlike every other router, this one is intentionally NOT protected by
``get_current_service`` — it is how a service obtains its first token.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.application.services.token_service import TokenService
from app.infrastructure.api.dependencies import token_service_dependency
from app.infrastructure.api.schemas.auth import (
    TokenRequest,
    TokenResponse,
    issued_token_to_response,
)
from app.infrastructure.api.schemas.common import ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_401 = {401: {"model": ErrorResponse, "description": "Invalid client credentials"}}


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses=_401,
    summary="Exchange client credentials for a service access token",
)
async def issue_token(
        body: TokenRequest,
        service: Annotated[TokenService, Depends(token_service_dependency)],
) -> TokenResponse:
    """Authenticate a service via client_id/client_secret and issue it a JWT."""
    token = service.authenticate_and_issue(body.client_id, body.client_secret)
    return issued_token_to_response(token)
