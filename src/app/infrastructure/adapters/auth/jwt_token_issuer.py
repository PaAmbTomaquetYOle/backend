"""JWT-based token issuer adapter."""

from datetime import datetime, timedelta, timezone

import jwt

from app.application.ports.token_issuer import IssuedToken, ITokenIssuer
from app.infrastructure.config.settings import Settings


class JwtTokenIssuer(ITokenIssuer):
    """Mints HS256 JWTs signed with the shared backend JWT secret."""

    def __init__(self, settings: Settings) -> None:
        """Initialize with the application settings.

        Args:
            settings: Settings holding the JWT secret, algorithm, audience, and expiry.
        """
        self._settings = settings

    def issue_token(self, client_id: str) -> IssuedToken:
        """Mint a new HS256 access token for the given service client.

        Args:
            client_id: Identifier of the service the token is issued to; becomes
                the token's ``iss`` claim.

        Returns:
            IssuedToken: The newly minted access token.
        """
        now = datetime.now(timezone.utc)
        expires_in = self._settings.token_expiry_seconds
        payload = {
            "iss": client_id,
            "aud": self._settings.jwt_audience,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        }
        access_token = jwt.encode(
            payload, self._settings.jwt_secret, algorithm=self._settings.jwt_algorithm
        )
        return IssuedToken(access_token=access_token, expires_in=expires_in)
