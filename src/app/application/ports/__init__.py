"""Outbound (driven) ports of the application layer.

A port is an abstraction that describes something the use cases *need from the
outside world*: a Slack gateway, an LLM client, a persistence repository, etc.
The application depends on these abstractions; the concrete implementations
(adapters) live in ``app.infrastructure.adapters`` and are wired in at the
composition root. This is what keeps the dependency rule pointing inward.

What goes here:
- One module per port, each defining an abstract contract as an ``abc.ABC`` or a
  ``typing.Protocol`` (e.g. ``SlackGatewayPort``, ``LlmClientPort``).

How it interacts:
- ``application.services`` import these ports and program against them.
- ``infrastructure.adapters`` implement them.

What does NOT go here:
- Concrete implementations, framework types (FastAPI/pydantic), or the services'
  own contracts (those belong in ``service_interfaces``).
- Distinguish from ``domain`` ports, which are expressed in pure domain language;
  ports here describe the application's needs from external systems.

Empty for now. As ports are added, export them here and list them in ``__all__``.
"""

from .annual_review_process import IAnnualReviewProcessRepository
from .dossier import DossierSearchResult, IDossierRepository
from .event_publisher import IEventPublisher
from .graph_database import IGraphDatabasePort
from .interview import IInterviewRepository
from .knowledge_graph import IKnowledgeGraphRepository
from .monthly_review_process import IMonthlyReviewProcessRepository
from .offboarding_process import IOffboardingProcessRepository

__all__: list[str] = [
    "DossierSearchResult",
    "IAnnualReviewProcessRepository",
    "IDossierRepository",
    "IEventPublisher",
    "IGraphDatabasePort",
    "IInterviewRepository",
    "IKnowledgeGraphRepository",
    "IMonthlyReviewProcessRepository",
    "IOffboardingProcessRepository",
]

