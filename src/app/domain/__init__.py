"""Domain layer: pure business logic, entities, value objects and ports.

This is the innermost layer and the heart of the system. It models the business
in plain Python and depends on *nothing* outside the standard library — no
FastAPI, no pydantic-settings, no external SDKs, no I/O. Both ``application`` and
``infrastructure`` may depend on it; it depends on neither of them.

What goes here:
- Entities and aggregates (objects with identity and invariants).
- Value objects (immutable, equality by value).
- Domain ports: interfaces expressed in pure domain language (e.g. a repository
  for an aggregate), defining what the domain needs without naming a technology.
- Domain services and domain events that encode business rules.

What does NOT go here:
- Frameworks or I/O of any kind, configuration, HTTP/persistence concerns, or
  use-case orchestration (that is ``application``).

Distinguish domain ports from ``application.ports``: domain ports speak the
business vocabulary, while application ports describe what the use cases need
from external systems.

Empty for now. As domain types are added, export them here and list them in
``__all__``.
"""

__all__: list[str] = []
