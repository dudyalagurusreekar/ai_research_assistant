"""Unit tests for Session Orchestrator."""

import unittest
from core.events import AsyncEventBus
from core.registry import CapabilityRegistry
from core.routing import CapabilityRouter
from core.orchestrator import SessionOrchestrator
from core.models import Request, SessionState, ResponseStatus
from tests.core.test_registry import DummyTool


class TestSessionOrchestrator(unittest.IsolatedAsyncioTestCase):
    """Test session lifecycle tracking and request coordination."""

    async def test_session_lifecycle_and_events(self):
        bus = AsyncEventBus()
        registry = CapabilityRegistry()
        router = CapabilityRouter(registry)
        orchestrator = SessionOrchestrator(event_bus=bus, registry=registry, router=router)

        events_captured = []

        async def event_listener(evt):
            events_captured.append(evt.event_type)

        bus.subscribe("*", event_listener)

        session = await orchestrator.create_session(user_id="user_101")
        self.assertEqual(session.state, SessionState.CREATED)

        await orchestrator.update_session_state(session.session_id, SessionState.RUNNING)
        self.assertEqual(session.state, SessionState.RUNNING)

        self.assertIn("session.created", events_captured)
        self.assertIn("session.state_changed", events_captured)

    async def test_process_request_workflow(self):
        bus = AsyncEventBus()
        registry = CapabilityRegistry()
        tool1 = DummyTool("calculator", ["math"])
        registry.register_tool(tool1)

        router = CapabilityRouter(registry)
        orchestrator = SessionOrchestrator(event_bus=bus, registry=registry, router=router)

        session = await orchestrator.create_session(user_id="user_202")
        req = Request(intent="Perform math calculation", session_id=session.session_id, parameters={"tool_name": "calculator"})

        response = await orchestrator.process_request(req)
        self.assertEqual(response.status, ResponseStatus.SUCCESS)
        self.assertEqual(response.session_id, session.session_id)
        self.assertEqual(session.state, SessionState.COMPLETED)


if __name__ == "__main__":
    unittest.main()
