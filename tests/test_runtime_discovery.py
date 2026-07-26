import unittest
from unittest.mock import MagicMock
from pathlib import Path
from agents.runtime.discovery import RuntimeCapabilityManager

class TestRuntimeDiscovery(unittest.TestCase):
    def test_get_installed_packages(self):
        manager = RuntimeCapabilityManager()
        pkgs = manager.get_installed_packages()
        self.assertIsInstance(pkgs, list)
        self.assertTrue(len(pkgs) > 0)

    def test_discover_capabilities(self):
        agent = MagicMock()
        agent.tools = {}
        agent.max_steps = 3
        agent.planning_interval = None
        agent.max_print_outputs_length = 1000

        manager = RuntimeCapabilityManager(agent)
        caps = manager.discover_capabilities()
        
        self.assertIn("python_version", caps)
        self.assertEqual(caps["execution_limits"]["max_steps"], 3)
        self.assertEqual(caps["execution_limits"]["max_print_outputs_length"], 1000)

    def test_generate_capability_prompt(self):
        mock_tool = MagicMock()
        mock_tool.name = "mock_test_tool"
        mock_tool.description = "A dummy description"
        
        def dummy_forward(arg1: str, arg2: int = 5):
            pass
        mock_tool.forward = dummy_forward

        agent = MagicMock()
        agent.tools = {"mock_test_tool": mock_tool}
        agent.max_steps = 5

        manager = RuntimeCapabilityManager(agent)
        prompt = manager.generate_capability_prompt()

        self.assertIn("mock_test_tool", prompt)
        self.assertIn("arg1: str (required)", prompt)
        self.assertIn("arg2: int", prompt)
        self.assertIn("Max Steps: 5", prompt)
