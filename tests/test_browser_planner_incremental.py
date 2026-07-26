import unittest
from unittest.mock import MagicMock, patch
from tools.browser.planner.planner import BrowserPlanner, PlannerResult
from tools.browser.models.response import ActionResult

class TestBrowserPlannerIncremental(unittest.TestCase):
    @patch("litellm.completion")
    def test_planner_incremental_execution(self, mock_completion) -> None:
        mock_browser = MagicMock()
        
        # Configure mock browser behavior
        mock_browser.get_current_url.return_value = MagicMock(success=True, data="https://google.com")
        mock_browser.get_page_title.return_value = MagicMock(success=True, data="Google")
        mock_browser.get_page_html.return_value = MagicMock(success=True, data="<html></html>")
        
        # Mock LLM calls:
        # Step 1: LLM returns macro_search action
        # Step 2: LLM returns finish action
        mock_resp_1 = MagicMock()
        mock_resp_1.choices = [
            MagicMock(message=MagicMock(content='{"thought": "I will search for AI.", "action": "macro_search", "query": "AI"}'))
        ]
        mock_resp_1.usage = MagicMock(total_tokens=100)
        
        mock_resp_2 = MagicMock()
        mock_resp_2.choices = [
            MagicMock(message=MagicMock(content='{"thought": "Search finished, reporting result.", "action": "finish", "answer": "Artificial intelligence is..."}'))
        ]
        mock_resp_2.usage = MagicMock(total_tokens=50)
        
        mock_completion.side_effect = [mock_resp_1, mock_resp_2]
        
        planner = BrowserPlanner(mock_browser)
        
        # Mock underlying action execution
        planner.executor.execute = MagicMock(return_value=ActionResult(
            url="https://google.com/search?q=AI", 
            title="AI - Search", 
            success=True, 
            data="results"
        ))
        
        res = planner.execute("Search about Artificial Intelligence", max_steps=5)
        
        self.assertTrue(res.success)
        self.assertEqual(res.final_output, "Artificial intelligence is...")
        self.assertEqual(res.steps_taken, 1) # 1 executable step, finish exits
        self.assertIsNotNone(res.report)
        self.assertEqual(res.report["metrics"]["tokens"]["total_tokens"], 150)
