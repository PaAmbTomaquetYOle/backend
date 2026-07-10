"""Enum of valid dossier states."""

from enum import Enum


class DossierStateEnum(Enum):
    """Enumeration of possible dossier lifecycle states."""
    NOT_GENERATED = "not_generated"
    GENERATING = "generating"
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    CANCELLED = "cancelled"
