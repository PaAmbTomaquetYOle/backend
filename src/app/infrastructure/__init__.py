"""Infrastructure layer: adapters to the outside world.

This is the outermost layer. It contains everything technology-specific —
the web framework, configuration loading, persistence, and clients for external
services — and it depends on the inner layers (``application`` and ``domain``),
never the other way around. It is where abstract ports become concrete.

Subpackages:
- ``api`` — the HTTP delivery mechanism (FastAPI routers and dependency wiring).
- ``config`` — environment-driven application settings.
- ``adapters`` — concrete implementations of ``application.ports`` (and domain
  ports): Slack clients, LLM clients, repositories, etc.

What does NOT go here:
- Business rules or use-case orchestration. Infrastructure should be a thin shell
  that translates between the outside world and the application layer.
"""

__all__: list[str] = []
