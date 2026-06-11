"""Root package for the Slack Agent backend.

This is the top-level namespace for the whole backend. Its only direct module is
``main.py``, which acts as the *composition root*: it creates the FastAPI
application and wires the layers together. Everything else lives in the three
architectural subpackages, ordered by the dependency rule (inner layers never
import outer ones):

- ``domain`` — pure business logic (innermost; depends on nothing).
- ``application`` — use cases that orchestrate the domain through ports.
- ``infrastructure`` — adapters to the outside world (web, config, clients).

What goes here:
- ``main.py`` only. New behaviour belongs in one of the layer subpackages.

What does NOT go here:
- Business logic, framework wiring or configuration outside ``main.py``.

Note: ``create_app``/``app`` from ``main`` are intentionally NOT re-exported. The
module-level ``app = create_app()`` runs as an import side effect, so importing
``app`` (the package) must stay cheap and free of that effect. Import the
application object explicitly via ``app.main:app`` (e.g. for uvicorn).
"""

__all__: list[str] = []
