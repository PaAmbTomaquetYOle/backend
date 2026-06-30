"""DRAFT state: dossier has been generated and is ready for review."""

from __future__ import annotations

from app.domain.dossier.state.base import DossierState
from app.domain.dossier.state.cancelled import CancelledDossierState
from app.domain.dossier.state.under_review import UnderReviewDossierState
from app.domain.enums import DossierStateEnum


class DraftDossierState(DossierState):
    """Dossier is a draft, ready for review submission."""

    def get_state(self) -> DossierStateEnum:
        """Returns the DRAFT state enum value."""
        return DossierStateEnum.DRAFT

    def submit_for_review(self) -> DossierState:
        """Transition to UNDER_REVIEW.

        Returns:
            DossierState: The new UnderReviewDossierState instance.
        """
        return UnderReviewDossierState()

    def cancel(self) -> DossierState:
        """Transition to CANCELLED.

        Returns:
            DossierState: The new CancelledDossierState instance.
        """
        return CancelledDossierState()
