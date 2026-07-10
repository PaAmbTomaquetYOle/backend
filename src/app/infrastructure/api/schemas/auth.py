"""Request/response schemas for the token endpoint."""

from typing import Literal

from pydantic import BaseModel

from app.application.ports.token_issuer import IssuedToken


class TokenRequest(BaseModel):
    """Request body for the client-credentials token grant."""

    grant_type: Literal["client_credentials"]
    client_id: str
    client_secret: str


class TokenResponse(BaseModel):
    """Response body representing an issued access token."""

    access_token: str
    token_type: str
    expires_in: int


def issued_token_to_response(token: IssuedToken) -> TokenResponse:
    """Convert an IssuedToken to its API response schema.

    Args:
        token: The issued token to serialize.

    Returns:
        TokenResponse: The corresponding response schema.
    """
    return TokenResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
    )
