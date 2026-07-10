"""Application service for the client-credentials token flow."""

from app.application.ports.service_credential_repository import IServiceCredentialRepository
from app.application.ports.token_issuer import IssuedToken, ITokenIssuer
from app.domain.exceptions.auth import InvalidCredentialsError


class TokenService:
    """Authenticates a service client and issues it an access token."""

    def __init__(
            self,
            credential_repository: IServiceCredentialRepository,
            token_issuer: ITokenIssuer,
    ) -> None:
        """Set up the service with its collaborators.

        Args:
            credential_repository: Verifies client_id/client_secret pairs.
            token_issuer: Mints access tokens for verified clients.
        """
        self._credential_repository = credential_repository
        self._token_issuer = token_issuer

    def authenticate_and_issue(self, client_id: str, client_secret: str) -> IssuedToken:
        """Verify a service client's credentials and issue it an access token.

        Args:
            client_id: Identifier of the service requesting a token.
            client_secret: Secret presented by the service.

        Returns:
            IssuedToken: The newly minted access token.

        Raises:
            InvalidCredentialsError: If the client_id/client_secret pair is invalid.
        """
        if not self._credential_repository.verify(client_id, client_secret):
            raise InvalidCredentialsError()
        return self._token_issuer.issue_token(client_id)
