"""CANCELLED state: dossier has been cancelled. Terminal state."""

from __future__ import annotations

from app.domain.dossier.state.base import DossierState
from app.domain.enums import DossierStateEnum


class CancelledDossierState(DossierState):
    """Dossier has been cancelled. Terminal state."""

    def get_state(self) -> DossierStateEnum:
        return DossierStateEnum.CANCELLED
