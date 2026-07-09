"""Service credential repository port — abstract interface for verifying client credentials."""

from abc import ABC, abstractmethod


class IServiceCredentialRepository(ABC):
    """Abstract interface for verifying service client-credentials pairs."""

    @abstractmethod
    def verify(self, client_id: str, client_secret: str) -> bool:
        """Check whether the given client_id/client_secret pair is valid.

        Args:
            client_id: Identifier of the service requesting a token.
            client_secret: Secret presented by the service.

        Returns:
            bool: True if the pair is valid, False otherwise.
        """
