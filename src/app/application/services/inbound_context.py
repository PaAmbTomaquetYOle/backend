"""Per-message context passed to inbound event handlers.

The Kafka consumer builds one of these per message (mirroring how FastAPI
builds a facade per HTTP request via Depends), bundling every bounded-context
service an inbound handler might need. Adding a new bounded context to the
inbound flow means adding a field here, not changing the handler port.
"""

from dataclasses import dataclass

from app.application.service_interfaces.knowledge_graph_service_interface import (
    IKnowledgeGraphService,
)
from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.service_interfaces.sop_service_interface import ISopService


@dataclass
class InboundContext:
    """Bundles the use-case services available to inbound event handlers."""

    offboarding: IOffboardingServiceFacade
    sops: ISopService
    knowledge_graph: IKnowledgeGraphService
