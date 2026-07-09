"""Token issuer port — abstract interface for minting service access tokens."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class IssuedToken:
    """A freshly minted access token returned to a service client."""

    access_token: str
    expires_in: int
    token_type: str = "Bearer"


class ITokenIssuer(ABC):
    """Abstract interface for issuing access tokens to authenticated services."""

    @abstractmethod
    def issue_token(self, client_id: str) -> IssuedToken:
        """Mint a new access token for the given service client.

        Args:
            client_id: Identifier of the service the token is issued to; becomes
                the token's ``iss`` claim.

        Returns:
            IssuedToken: The newly minted access token.
        """
