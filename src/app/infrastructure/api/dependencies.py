"""FastAPI dependency wiring (composition of ports and adapters).

This module is the place to assemble use cases with their concrete adapters and
expose them as FastAPI dependencies via ``Depends``. It is intentionally empty
for now and will grow as bounded contexts (Slack, LLM agent, ...) are added.
"""

from app.infrastructure.config.settings import Settings, get_settings


def settings_dependency() -> Settings:
    """Expose application settings as a FastAPI dependency."""
    return get_settings()
