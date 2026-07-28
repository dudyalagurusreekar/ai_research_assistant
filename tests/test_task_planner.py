"""Unit and Integration Tests for the Browser Task Planner.

Validates graph structure, cycles, topological sorting, optimizations, and execution flows
including branching routing, loops, retries, and error handling.
"""

import unittest
from typing import Dict, Any

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.core.browser import Browser
from tools.browser.models.response import ActionResult
from tools.browser.planner.graph import TaskGraph, TaskNode, TaskStatus
from tools.browser.planner.engine import TaskPlannerEngine
from tests.test_browser_action_engine import LocalHTTPTestServer


class TestTaskGraph(unittest.TestCase):
    """Unit tests validating TaskNode and TaskGraph operations."""

    def test_cycle_detection(self):
        """Verify cyclic dependency detection throws errors."""
        graph = TaskGraph()
        
        # A depends on B, B depends on C, C depends on A
        graph.add_node(TaskNode(node_id="A", name="Task A", action="open_url", params={"url": "http://test.com"}))
        graph.add_node(TaskNode(node_id="B", name="Task B", action="click", params={"selector": "#btn"}))
        graph.add_node(TaskNode(node_id="C", name="Task C", action="fill_input", params={"selector": "#input", "text_input": "hello"}))
        
        graph.add_dependency(from_id="B", to_id="A")
        graph.add_dependency(from_id="C", to_id="B")
        graph.add_dependency(from_id="A", to_id="C")

        errors = graph.validate()
        self.assertTrue(any("Cyclic dependency" in err for err in errors))

    def test_missing_dependency(self):
        """Verify missing dependency detection throws errors."""
        graph = TaskGraph()
        graph.add_node(TaskNode(node_id="A", name="Task A", action="open_url", params={"url": "http://test.com"}))
        graph.add_dependency(from_id="MissingTask", to_id="A")

        errors = graph.validate()
        self.assertTrue(any("MissingTask" in err for err in errors))

    def test_action_validation(self):
        """Verify missing parameters triggers validation errors."""
        graph = TaskGraph()
        graph.add_node(TaskNode(node_id="A", name="Task A", action="open_url", params={})) # Missing url
        graph.add_node(TaskNode(node_id="B", name="Task B", action="click", params={})) # Missing selector

        errors = graph.validate()
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("missing required 'url' param" in err for err in errors))
        self.assertTrue(any("missing required 'selector' param" in err for err in errors))

    def test_optimization_redundant_urls(self):
        """Verify redundant consecutive open_url calls are skipped."""
        graph = TaskGraph()
        graph.add_node(TaskNode(node_id="nav1", name="Navigate 1", action="open_url", params={"url": "http://test.com"}))
        graph.add_node(TaskNode(node_id="nav2", name="Navigate 2", action="open_url", params={"url": "http://test.com"}))
        graph.add_dependency(from_id="nav1", to_id="nav2")

        graph.optimize()
        self.assertEqual(graph.nodes["nav1"].status, TaskStatus.PENDING)
        self.assertEqual(graph.nodes["nav2"].status, TaskStatus.SKIPPED)

    def test_optimization_redundant_clear(self):
        """Verify clear_input followed by fill_input is optimized away."""
        graph = TaskGraph()
        graph.add_node(TaskNode(node_id="clear", name="Clear field", action="clear_input", params={"selector": "#username"}))
        graph.add_node(TaskNode(node_id="fill", name="Fill field", action="fill_input", params={"selector": "#username", "text_input": "alice"}))
        graph.add_dependency(from_id="clear", to_id="fill")

        graph.optimize()
        self.assertEqual(graph.nodes["clear"].status, TaskStatus.SKIPPED)
        self.assertEqual(graph.nodes["fill"].status, TaskStatus.PENDING)
        # Verify clear's dependency was removed from fill
        self.assertNotIn("clear", graph.nodes["fill"].dependencies)

    def test_optimization_scroll_consolidation(self):
        """Verify consecutive scrolls in same direction are consolidated."""
        graph = TaskGraph()
        graph.add_node(TaskNode(node_id="s1", name="Scroll 1", action="scroll_page", params={"selector": "#div", "scroll_direction": "down", "scroll_amount": 300}))
        graph.add_node(TaskNode(node_id="s2", name="Scroll 2", action="scroll_page", params={"selector": "#div", "scroll_direction": "down", "scroll_amount": 400}))
        graph.add_dependency(from_id="s1", to_id="s2")

        graph.optimize()
        self.assertEqual(graph.nodes["s1"].status, TaskStatus.SKIPPED)
        self.assertEqual(graph.nodes["s2"].status, TaskStatus.PENDING)
        self.assertEqual(graph.nodes["s2"].params["scroll_amount"], 700)


class MockExecutor:
    """Mock Executor that simulates action responses without actual browser drivers."""

    def __init__(self):
        self.calls = []
        self.results = {}

    def execute(self, action_dict: Dict[str, Any]) -> ActionResult:
        self.calls.append(action_dict)
        action = action_dict.get("action")
        if action in self.results:
            return self.results[action]
        return ActionResult(url="about:blank", title="", success=True)


class TestTaskPlannerEngine(unittest.TestCase):
    """Unit and Integration tests for TaskPlannerEngine workflow execution."""

    @classmethod
    def setUpClass(cls):
        cls.server = LocalHTTPTestServer()
        cls.server.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self):
        self.config = BrowserConfig(
            engine_type=BrowserEngineType.PLAYWRIGHT,
            headless=True,
            timeout_seconds=5.0,
            max_retries=0,
        )
        self.browser = Browser(config=self.config)
        self.engine = TaskPlannerEngine(self.browser)

    def tearDown(self):
        self.browser.close()

    def test_engine_execution_branching_true(self):
        """Verify routing then_node when branching condition is True."""
        graph = TaskGraph()
        
        # Node 1: Navigate
        graph.add_node(TaskNode(node_id="nav", name="Navigate", action="open_url", params={"url": self.base_url}))
        
        # Node 2: Check conditional element exists (username exists on test page)
        graph.add_node(TaskNode(
            node_id="check_login",
            name="Check field condition",
            action="click", # unused but action required
            params={"selector": "#username"},
            dependencies=["nav"],
            condition={
                "type": "element_exists",
                "selector": "#username",
                "then_node": "fill_user",
                "else_node": "skip_user"
            }
        ))
        
        # Branch A
        graph.add_node(TaskNode(node_id="fill_user", name="Fill username", action="fill_input", params={"selector": "#username", "text_input": "branch_true"}, dependencies=["check_login"]))
        
        # Branch B
        graph.add_node(TaskNode(node_id="skip_user", name="Skip action", action="click", params={"selector": "#submit-btn"}, dependencies=["check_login"]))

        # Execute
        res = self.engine.execute_plan(graph)
        self.assertTrue(res["success"])
        
        # Since element `#username` exists, then_node "fill_user" should be COMPLETED
        self.assertEqual(graph.nodes["fill_user"].status, TaskStatus.COMPLETED)
        # else_node "skip_user" should be SKIPPED
        self.assertEqual(graph.nodes["skip_user"].status, TaskStatus.SKIPPED)

    def test_engine_execution_branching_false(self):
        """Verify routing else_node when branching condition is False."""
        graph = TaskGraph()
        
        # Node 1: Navigate
        graph.add_node(TaskNode(node_id="nav", name="Navigate", action="open_url", params={"url": self.base_url}))
        
        # Node 2: Check condition for a non-existent element
        graph.add_node(TaskNode(
            node_id="check_login",
            name="Check field condition",
            action="click",
            params={"selector": "#non-existent"},
            dependencies=["nav"],
            condition={
                "type": "element_exists",
                "selector": "#non-existent",
                "then_node": "fill_user",
                "else_node": "skip_user"
            }
        ))
        
        # Branch A
        graph.add_node(TaskNode(node_id="fill_user", name="Fill username", action="fill_input", params={"selector": "#username", "text_input": "branch_false"}, dependencies=["check_login"]))
        
        # Branch B
        graph.add_node(TaskNode(node_id="skip_user", name="Skip action", action="click", params={"selector": "#submit-btn"}, dependencies=["check_login"]))

        # Execute
        res = self.engine.execute_plan(graph)
        self.assertTrue(res["success"])
        
        # Since element `#non-existent` does not exist, then_node "fill_user" should be SKIPPED
        self.assertEqual(graph.nodes["fill_user"].status, TaskStatus.SKIPPED)
        # else_node "skip_user" should be COMPLETED
        self.assertEqual(graph.nodes["skip_user"].status, TaskStatus.COMPLETED)

    def test_engine_retries_and_failure_propagation(self):
        """Verify execution retries on failure, and failure propagates downstream."""
        graph = TaskGraph()
        
        # Node A: Fails (non-existent button click)
        # Set max_retries = 1
        graph.add_node(TaskNode(node_id="fail_node", name="Click invalid btn", action="click", params={"selector": "#invalid-btn"}, max_retries=1))
        
        # Node B: Depends on A
        graph.add_node(TaskNode(node_id="dependent_node", name="Dependent task", action="get_clean_text", dependencies=["fail_node"]))

        # Execute
        res = self.engine.execute_plan(graph)
        
        # Plan success should be False
        self.assertFalse(res["success"])
        # fail_node should have retry_count = 1 and status = FAILED
        self.assertEqual(graph.nodes["fail_node"].retry_count, 1)
        self.assertEqual(graph.nodes["fail_node"].status, TaskStatus.FAILED)
        # dependent_node should have been SKIPPED due to parent failure
        self.assertEqual(graph.nodes["dependent_node"].status, TaskStatus.SKIPPED)


if __name__ == "__main__":
    unittest.main()
