"""Application configuration, driven by the environment.

This package centralises how the backend is configured. Settings are read from
the environment (and a local ``.env`` file) via pydantic-settings and exposed as
a single, cached ``Settings`` instance so the rest of the app reads configuration
through one typed object instead of touching ``os.environ`` directly.

What goes here:
- ``settings.py`` — the ``Settings`` model and the ``get_settings`` cached
  factory.

How it interacts:
- ``app.infrastructure.api.dependencies`` exposes settings to endpoints; ``main``
  uses them to build the app; adapters read credentials/endpoints from here.

What does NOT go here:
- Hard-coded secrets (provide them via the environment) or business logic.
"""

from app.infrastructure.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
