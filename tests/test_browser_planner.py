"""Unit and Integration Tests for the AI Browser Planner.

Covers DOM simplification, execution state tracking, prompts, and planner loop orchestration.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.core.browser import Browser
from tools.browser.planner.simplifier import DOMSimplifier
from tools.browser.planner.state import PlannerState
from tools.browser.planner.planner import BrowserPlanner, PlannerResult


class TestDOMSimplifier(unittest.TestCase):
    """Verify DOMSimplifier interactive node extraction and selector mapping."""

    def test_dom_simplifier_extraction(self):
        simplifier = DOMSimplifier()
        html = """
        <html>
        <body>
            <h1>Doc title</h1>
            <a href="https://example.com/link">Example Link</a>
            <input type="text" id="username" name="user" placeholder="Enter Username" />
            <input type="hidden" name="token" value="secret" />
            <button class="btn" type="submit">Click Me</button>
            <div style="display: none;"><button>Hidden Button</button></div>
        </body>
        </html>
        """
        result = simplifier.simplify(html)
        
        # Verify text representation content
        self.assertIn("A", result)
        self.assertIn("INPUT", result)
        self.assertIn("BUTTON", result)
        # Verify hidden elements are excluded
        self.assertNotIn("Hidden Button", result)
        self.assertNotIn("token", result)

        # Verify selector mappings
        self.assertEqual(simplifier.get_selector(1), "html > body > a")
        self.assertEqual(simplifier.get_selector(2), "#username")
        self.assertEqual(simplifier.get_selector(3), "html > body > button")


class TestPlannerState(unittest.TestCase):
    """Verify execution tracking and summary formatting."""

    def test_planner_state_tracking(self):
        state = PlannerState("Search React docs")
        self.assertEqual(state.goal, "Search React docs")
        self.assertEqual(state.current_step, 1)

        # Record first step
        state.add_step(
            thought="Navigate to homepage",
            command="open_url",
            selector=None,
            text="https://react.dev",
            result_message="Page loaded successfully",
            success=True,
            duration_ms=250.0
        )
        self.assertEqual(state.current_step, 2)
        self.assertEqual(len(state.history), 1)

        # Record second step as failed
        state.add_step(
            thought="Click button",
            command="click",
            selector="#btn",
            text=None,
            result_message="Button not clickable",
            success=False,
            duration_ms=100.0
        )
        self.assertEqual(state.current_step, 3)
        self.assertEqual(len(state.errors), 1)
        self.assertIn("Button not clickable", state.errors)

        summary = state.get_summary_text()
        self.assertIn("Step 1:", summary)
        self.assertIn("Step 2:", summary)
        self.assertIn("FAILED", summary)


class TestBrowserPlanner(unittest.TestCase):
    """Verify core planner loop coordination and tool dispatch integration."""

    def setUp(self) -> None:
        self.config = BrowserConfig(engine_type=BrowserEngineType.MOCK)
        self.browser = Browser(self.config)

    def tearDown(self) -> None:
        self.browser.close()

    @patch("litellm.completion")
    def test_browser_planner_execution_loop(self, mock_completion):
        # Configure a sequence of mock LLM decisions
        mock_response_1 = MagicMock()
        mock_response_1.choices[0].message.content = """
        {
            "thought": "I need to open the React homepage.",
            "action": "open_url",
            "url": "https://react.dev"
        }
        """
        
        mock_response_2 = MagicMock()
        mock_response_2.choices[0].message.content = """
        {
            "thought": "I will click the search input element.",
            "action": "click",
            "ref_id": 1
        }
        """

        mock_response_3 = MagicMock()
        mock_response_3.choices[0].message.content = """
        {
            "thought": "Goal achieved. I extracted the useEffect details.",
            "action": "finish",
            "answer": "useEffect is a React Hook that lets you synchronize a component with an external system."
        }
        """

        mock_completion.side_effect = [mock_response_1, mock_response_2, mock_response_3]

        planner = BrowserPlanner(self.browser)
        res = planner.execute("Search useEffect in React docs", max_steps=5)

        self.assertTrue(res.success)
        self.assertEqual(res.steps_taken, 2)
        self.assertIn("lets you synchronize a component", res.final_output)

    def test_browser_tool_plan_dispatch(self):
        """Verify BrowserTool routes 'plan' action correctly."""
        from tools.browser.tool import BrowserTool
        tool = BrowserTool(browser=self.browser)

        # Patch the planner to return a mock result directly to prevent actual LLM completion calls
        with patch("tools.browser.planner.planner.BrowserPlanner.execute") as mock_exec:
            mock_exec.return_value = PlannerResult(
                success=True,
                goal="Search docs",
                steps_taken=3,
                final_output="Found page",
                duration_ms=450.0,
                errors=[]
            )

            res_str = tool.forward(action="plan", text_input="Search docs")
            res_dict = json.loads(res_str)

            self.assertTrue(res_dict["success"])
            self.assertEqual(res_dict["final_output"], "Found page")
            self.assertEqual(res_dict["steps_taken"], 3)


if __name__ == "__main__":
    unittest.main()
