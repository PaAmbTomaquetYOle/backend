"""FastAPI routers, grouped by bounded context.

Each module here defines an ``APIRouter`` exposing a cohesive set of endpoints
(health, Slack, agent, ...). ``app.main`` includes these routers when it builds
the application.

What goes here:
- One module per context (e.g. ``health.py``, later ``slack.py``), each defining
  a ``router``.

How it interacts:
- Endpoints obtain their collaborators via ``Depends`` from
  ``app.infrastructure.api.dependencies`` — they do not instantiate services or
  adapters themselves.

What does NOT go here:
- Business logic, dependency construction, or direct use of external SDKs.
"""

from app.infrastructure.api.routers import health

__all__ = ["health"]
