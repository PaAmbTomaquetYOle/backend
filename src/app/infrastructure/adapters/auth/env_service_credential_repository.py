"""Environment-backed service credential repository."""

import secrets

from app.application.ports.service_credential_repository import IServiceCredentialRepository
from app.infrastructure.config.settings import Settings


class EnvServiceCredentialRepository(IServiceCredentialRepository):
    """Verifies client credentials against the SERVICE_CREDENTIALS setting."""

    def __init__(self, settings: Settings) -> None:
        """Initialize with the application settings.

        Args:
            settings: Settings holding the service_credentials mapping.
        """
        self._settings = settings

    def verify(self, client_id: str, client_secret: str) -> bool:
        """Check the given client_id/client_secret pair against configured secrets.

        Uses a constant-time comparison to avoid leaking timing information
        about the stored secret.

        Args:
            client_id: Identifier of the service requesting a token.
            client_secret: Secret presented by the service.

        Returns:
            bool: True if the pair matches a configured service credential.
        """
        expected_secret = self._settings.service_credentials.get(client_id)
        if not expected_secret:
            return False
        return secrets.compare_digest(expected_secret, client_secret)
