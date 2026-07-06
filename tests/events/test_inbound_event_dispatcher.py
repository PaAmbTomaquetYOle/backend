"""Tests for InboundEventDispatcher."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.services.inbound_event_dispatcher import (
    InboundEventDispatcher,
    UnknownEventTypeError,
)
from app.domain.events.base import DomainEvent


def _handler(event_type: str) -> AsyncMock:
    handler = AsyncMock()
    handler.event_type = event_type
    return handler


class TestInboundEventDispatcher:
    def test_rejects_duplicate_event_type(self) -> None:
        with pytest.raises(ValueError):
            InboundEventDispatcher([_handler("a"), _handler("a")])

    @pytest.mark.anyio
    async def test_dispatch_routes_to_matching_handler(self) -> None:
        handler_a = _handler("a")
        handler_b = _handler("b")
        dispatcher = InboundEventDispatcher([handler_a, handler_b])
        event = DomainEvent(event_type="b", payload={}, event_id=uuid4())
        facade = object()

        await dispatcher.dispatch(event, facade)

        handler_b.handle.assert_awaited_once_with(event, facade)
        handler_a.handle.assert_not_awaited()

    @pytest.mark.anyio
    async def test_dispatch_raises_for_unknown_event_type(self) -> None:
        dispatcher = InboundEventDispatcher([_handler("a")])
        event = DomainEvent(event_type="unknown", payload={}, event_id=uuid4())

        with pytest.raises(UnknownEventTypeError):
            await dispatcher.dispatch(event, object())
