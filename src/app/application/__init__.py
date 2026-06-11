"""Application layer: use cases that orchestrate the domain through ports.

This layer holds the application-specific business rules: it coordinates domain
entities and value objects to fulfil use cases, but it knows nothing about HTTP,
databases or third-party SDKs. It may import from ``domain`` but must never
import from ``infrastructure`` (the dependency rule points inward).

Subpackages:
- ``services`` — the use-case orchestrators themselves. Each service behaves as a
  single shared instance (a "singleton") and implements a contract from
  ``service_interfaces``.
- ``service_interfaces`` — the abstract contracts that the services implement, so
  callers depend on an abstraction rather than a concrete class.
- ``ports`` — outbound (driven) ports: the abstractions the use cases need from
  the outside world (Slack gateways, LLM clients, repositories). Concrete
  implementations live in ``infrastructure/adapters``.

What does NOT go here:
- Framework code (FastAPI, pydantic-settings), concrete adapters, or pure domain
  rules (those belong in ``domain``).
"""

__all__: list[str] = []
