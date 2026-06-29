"""FastAPI dependency wiring (composition of ports and adapters).

This module is the place to assemble use cases with their concrete adapters and
expose them as FastAPI dependencies via ``Depends``. It will grow as bounded
contexts (Slack, LLM agent, ...) are added.
"""

from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.infrastructure.adapters.repositories.offboarding_process import (
    OffboardingProcessRepository,
)
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.persistence.database import get_session


def settings_dependency() -> Settings:
    """Expose application settings as a FastAPI dependency."""
    return get_settings()


def offboarding_repository_dependency(
    session: Annotated[Session, Depends(get_session)],
) -> OffboardingProcessRepository:
    """Provide a SQLModel-backed offboarding process repository."""
    return OffboardingProcessRepository(session)
