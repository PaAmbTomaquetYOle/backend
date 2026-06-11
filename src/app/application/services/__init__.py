"""Application services: the use-case orchestrators.

Each service coordinates domain logic and outbound ports to carry out a use case
(e.g. handling a Slack event, running an agent turn). Services depend on
abstractions only: they receive ``application.ports`` implementations through
their constructor and never touch external SDKs directly.

Two rules every service in this package must follow:

1. **Behave as a singleton.** Not the classic Singleton pattern (no private
   constructor, no ``__new__`` trickery, no global mutable state guard). It
   simply means the service is *instantiated once* and that single instance is
   shared everywhere — built by a cached factory (``functools.lru_cache``) or
   assembled once at the composition root and injected via FastAPI ``Depends``.
   Services are therefore expected to be stateless (or to hold only
   safely-shared state).

2. **Implement an interface from** ``app.application.service_interfaces``. The
   concrete service subclasses / satisfies its contract there, so routers and
   other services can depend on the abstraction instead of the concrete class.

What goes here:
- One module per service (e.g. ``slack_service.py`` defining ``SlackService``).

What does NOT go here:
- Framework code (FastAPI), direct use of external SDKs (go through
  ``application.ports``), or the contracts themselves (``service_interfaces``).

Empty for now. As services are added, export them here and list them in
``__all__``.
"""

__all__: list[str] = []
