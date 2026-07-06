"""Kafka topic naming convention shared by the producer and consumer adapters.

Topics are namespaced by direction so the consumer never re-processes events it
(or its peers) just produced:

- Outbound (backend -> slack-agent): ``{outbound_prefix}.{event_type}``, e.g.
  ``offboarding.dossier.generated``.
- Inbound (slack-agent -> backend): ``{inbound_prefix}.{event_type}``, e.g.
  ``slack-agent.offboarding.triggered``.
"""


def topic_name(prefix: str, event_type: str) -> str:
    """Build a Kafka topic name from a namespace prefix and a domain event type.

    Args:
        prefix: The namespace prefix for the topic (direction-specific).
        event_type: The domain event type, e.g. "interview.completed".

    Returns:
        str: The full topic name, e.g. "offboarding.interview.completed".
    """
    return f"{prefix}.{event_type}"
