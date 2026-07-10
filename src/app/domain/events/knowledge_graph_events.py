from .base import DomainEvent


def KnowledgeGraphUpdated(entity_type: str, entity_id: str, action: str) -> DomainEvent:
    return DomainEvent(
        event_type="knowledge_graph.updated",
        payload={
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
        },
    )
