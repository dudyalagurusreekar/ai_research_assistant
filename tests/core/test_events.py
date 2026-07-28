"""Unit tests for Async Event Bus."""

import unittest
from core.events import AsyncEventBus
from core.models import Event
from core.exceptions import EventError


class TestAsyncEventBus(unittest.IsolatedAsyncioTestCase):
    """Test pub/sub event dispatching."""

    async def test_publish_subscribe_sync_and_async(self):
        bus = AsyncEventBus()
        received_sync = []
        received_async = []

        def sync_handler(event: Event):
            received_sync.append(event.payload["val"])

        async def async_handler(event: Event):
            received_async.append(event.payload["val"])

        bus.subscribe("test.topic", sync_handler)
        bus.subscribe("test.topic", async_handler)

        event = Event(event_type="test.topic", source="unit_test", payload={"val": 42})
        await bus.publish(event)

        self.assertEqual(received_sync, [42])
        self.assertEqual(received_async, [42])

    async def test_unsubscribe(self):
        bus = AsyncEventBus()
        received = []

        def handler(event: Event):
            received.append(event.event_id)

        bus.subscribe("topic", handler)
        await bus.publish(Event(event_type="topic", source="test"))
        self.assertEqual(len(received), 1)

        bus.unsubscribe("topic", handler)
        await bus.publish(Event(event_type="topic", source="test"))
        self.assertEqual(len(received), 1)

    async def test_handler_error_raises_event_error(self):
        bus = AsyncEventBus()

        def broken_handler(event: Event):
            raise ValueError("Boom")

        bus.subscribe("broken", broken_handler)
        with self.assertRaises(EventError):
            await bus.publish(Event(event_type="broken", source="test"))


if __name__ == "__main__":
    unittest.main()
