"""Async Event Bus implementation."""

import inspect
import logging
from typing import Dict, Set
from core.interfaces.event_bus import EventHandler, IEventBus
from core.models.event import Event
from core.exceptions.base import EventError
from core.exceptions.codes import ErrorCode

logger = logging.getLogger("Core.EventBus")


class AsyncEventBus(IEventBus):
    """Decoupled asynchronous publish-subscribe event bus."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Set[EventHandler]] = {}
        self._logger = logger

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a synchronous or asynchronous handler to an event type.

        Args:
            event_type: String identifier of the event topic/type (e.g. 'session.created').
            handler: Callable taking an Event object.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = set()
        self._handlers[event_type].add(handler)
        self._logger.debug(f"Subscribed handler '{handler.__name__}' to event '{event_type}'.")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: String identifier of the event topic/type.
            handler: Previously subscribed handler callable.

        Returns:
            True if handler was found and removed, False otherwise.
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            self._logger.debug(f"Unsubscribed handler '{handler.__name__}' from event '{event_type}'.")
            return True
        return False

    async def publish(self, event: Event) -> None:
        """Publish an event asynchronously to all subscribed handlers.

        Wildcard topic '*' subscribers receive all published events.

        Args:
            event: Event model instance.
        """
        target_handlers: Set[EventHandler] = set()

        if event.event_type in self._handlers:
            target_handlers.update(self._handlers[event.event_type])
        if "*" in self._handlers:
            target_handlers.update(self._handlers["*"])

        if not target_handlers:
            self._logger.debug(f"No subscribers for event type '{event.event_type}'.")
            return

        for handler in target_handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self._logger.error(
                    f"Error in handler '{getattr(handler, '__name__', str(handler))}' "
                    f"processing event '{event.event_id}' ({event.event_type}): {e}",
                    exc_info=True,
                )
                raise EventError(
                    f"Handler execution failed for event '{event.event_type}'",
                    code=ErrorCode.SUBSCRIBER_ERROR,
                    context={"event_id": event.event_id, "event_type": event.event_type},
                    cause=e,
                ) from e
