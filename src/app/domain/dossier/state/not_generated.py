"""NOT_GENERATED state: dossier has not been generated yet."""

from __future__ import annotations

from app.domain.dossier.state.base import DossierState
from app.domain.dossier.state.cancelled import CancelledDossierState
from app.domain.dossier.state.generating import GeneratingDossierState
from app.domain.enums import DossierStateEnum


class NotGeneratedDossierState(DossierState):
    """Dossier has not yet been generated. Initial state."""

    def get_state(self) -> DossierStateEnum:
        return DossierStateEnum.NOT_GENERATED

    def start_generating(self) -> DossierState:
        return GeneratingDossierState()

    def cancel(self) -> DossierState:
        return CancelledDossierState()
