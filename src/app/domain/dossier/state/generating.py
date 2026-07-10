"""GENERATING state: dossier generation is in progress."""

from __future__ import annotations

from app.domain.dossier.state.base import DossierState
from app.domain.dossier.state.cancelled import CancelledDossierState
from app.domain.dossier.state.draft import DraftDossierState
from app.domain.enums import DossierStateEnum


class GeneratingDossierState(DossierState):
    """Dossier is being generated (e.g., AI processing)."""

    def get_state(self) -> DossierStateEnum:
        """Returns the GENERATING state enum value."""
        return DossierStateEnum.GENERATING

    def complete_generation(self) -> DossierState:
        """Transition to DRAFT.

        Returns:
            DossierState: The new DraftDossierState instance.
        """
        return DraftDossierState()

    def cancel(self) -> DossierState:
        """Transition to CANCELLED.

        Returns:
            DossierState: The new CancelledDossierState instance.
        """
        return CancelledDossierState()
