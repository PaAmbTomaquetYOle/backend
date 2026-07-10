"""HTTP endpoint for the client-credentials token grant.

Unlike every other router, this one is intentionally NOT protected by
``get_current_service`` — it is how a service obtains its first token.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.application.services.token_service import TokenService
from app.infrastructure.api.dependencies import token_service_dependency
from app.infrastructure.api.rate_limiter import limiter
from app.infrastructure.api.schemas.auth import (
    TokenRequest,
    TokenResponse,
    issued_token_to_response,
)
from app.infrastructure.api.schemas.common import ErrorResponse
from app.infrastructure.config.settings import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

_401 = {401: {"model": ErrorResponse, "description": "Invalid client credentials"}}


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses=_401,
    summary="Exchange client credentials for a service access token",
)
@limiter.limit(lambda: get_settings().auth_token_rate_limit)
async def issue_token(
        request: Request,
        body: TokenRequest,
        service: Annotated[TokenService, Depends(token_service_dependency)],
) -> TokenResponse:
    """Authenticate a service via client_id/client_secret and issue it a JWT.

    Rate-limited per client IP (see ``auth_token_rate_limit``) to slow down
    credential brute-forcing against ``SERVICE_CREDENTIALS``.
    """
    token = service.authenticate_and_issue(body.client_id, body.client_secret)
    return issued_token_to_response(token)
