"""Interface for event bus pub/sub communications."""

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Union
from core.models.event import Event

EventHandler = Callable[[Event], Union[None, Awaitable[None]]]


class IEventBus(ABC):
    """Abstract Interface for async publish-subscribe event bus."""

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers asynchronously."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to events of event_type."""

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """Unsubscribe a handler from event_type."""
