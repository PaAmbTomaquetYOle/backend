"""Contracts implemented by the application services.

This package defines the abstract interface of each service in
``app.application.services`` — its public API as an ``abc.ABC`` or a
``typing.Protocol``. Services implement these contracts so that their callers
(routers via ``Depends``, other services) can depend on the abstraction rather
than the concrete class, which keeps wiring swappable and tests easy to fake.

This package lives in the *application* layer (it was deliberately not placed in
``infrastructure``): a service and the contract it implements belong to the same
layer, so the dependency rule is preserved — ``application`` never reaches out
to ``infrastructure``.

What goes here:
- One module per contract (e.g. ``slack_service_interface.py`` defining
  ``SlackServiceInterface``). Interfaces only — abstract methods, no logic.

How it interacts:
- ``application.services`` implement these interfaces.
- Callers type their dependencies against them.

What does NOT go here:
- Concrete implementations (those are services), or outbound ports describing
  external systems (those are ``application.ports``).

Empty for now. As contracts are added, export them here and list them in
``__all__``.
"""

__all__: list[str] = []
