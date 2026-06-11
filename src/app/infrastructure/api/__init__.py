"""HTTP delivery layer (FastAPI): dependency wiring and routers.

This package is the inbound adapter for HTTP. It exposes the application's use
cases over the web and is the place where ports are composed with their concrete
adapters and handed to endpoints through FastAPI's ``Depends`` mechanism.

What goes here:
- ``dependencies.py`` — the composition of ports/adapters/services into FastAPI
  dependencies (the HTTP-side wiring).
- ``routers`` (subpackage) — the endpoint definitions, grouped by context.

How it interacts:
- Routers receive their collaborators via ``Depends`` from ``dependencies.py``;
  they call into ``application.services`` and translate results to HTTP.

What does NOT go here:
- Business logic or orchestration — endpoints stay thin and delegate to the
  application layer.
"""

from app.infrastructure.api.dependencies import settings_dependency

__all__ = ["settings_dependency"]
