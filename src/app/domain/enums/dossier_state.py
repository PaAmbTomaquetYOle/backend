from enum import Enum


class DossierStateEnum(Enum):
    NOT_GENERATED = "not_generated"
    GENERATING = "generating"
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    CANCELLED = "cancelled"
