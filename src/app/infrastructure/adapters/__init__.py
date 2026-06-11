"""Concrete adapters: implementations of the abstract ports.

An adapter is the technology-specific side of a port. For every abstraction the
application declares in ``app.application.ports`` (or the domain declares in
``app.domain``), a concrete class lives here that actually talks to the outside
world — the Slack Web API, an LLM provider, a database, etc.

What goes here:
- One module per adapter (e.g. ``slack_gateway.py`` implementing
  ``SlackGatewayPort``). These classes may freely use external SDKs and I/O.

How it interacts:
- Implements the ports defined inward, and is wired to the application at the
  composition root (see ``app.infrastructure.api.dependencies`` and
  ``app.main``).

What does NOT go here:
- Business logic or use-case orchestration (that is ``application``), and the
  port abstractions themselves (those live in the inner layers).

Empty for now. As adapters are added, export them here and list them in
``__all__``.
"""

__all__: list[str] = []
