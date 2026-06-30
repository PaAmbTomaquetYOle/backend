"""UNDER_REVIEW state: dossier has been submitted for manager review."""

from __future__ import annotations

from app.domain.dossier.state.approved import ApprovedDossierState
from app.domain.dossier.state.base import DossierState
from app.domain.dossier.state.cancelled import CancelledDossierState
from app.domain.enums import DossierStateEnum


class UnderReviewDossierState(DossierState):
    """Dossier is under manager review."""

    def get_state(self) -> DossierStateEnum:
        """Returns the UNDER_REVIEW state enum value."""
        return DossierStateEnum.UNDER_REVIEW

    def approve(self) -> DossierState:
        """Transition to APPROVED.

        Returns:
            DossierState: The new ApprovedDossierState instance.
        """
        return ApprovedDossierState()

    def cancel(self) -> DossierState:
        """Transition to CANCELLED.

        Returns:
            DossierState: The new CancelledDossierState instance.
        """
        return CancelledDossierState()
