import unittest
import tempfile
import os
import json
import time
from tools.browser.reporting_legacy import ReportingEngine, ExecutionReport
from tools.browser.planner.state import PlannerState

class TestBrowserReporting(unittest.TestCase):
    def test_report_generation_and_saving(self) -> None:
        state = PlannerState("Extract data from wikipedia")
        state.success = True
        state.total_tokens_used = 1200
        state.screenshots.append("screenshot1.png")
        state.artifacts.append("artifact1.json")
        state.errors.append("None")
        
        # Add a step
        state.add_step(
            thought="Navigate to wiki",
            command="open_url",
            selector=None,
            text="https://wikipedia.org",
            result_message="Page loaded",
            success=True,
            duration_ms=450.0,
            dom_simplify_time_ms=10.0,
            llm_inference_time_ms=80.0
        )
        
        start_time = time.time() - 2.0 # 2 seconds ago
        
        report = ReportingEngine.generate_report(
            task_id="task_test_123",
            goal="Extract data from wikipedia",
            planner_state=state,
            start_time=start_time,
            final_output="Wiki Data Output"
        )
        
        self.assertEqual(report.task_id, "task_test_123")
        self.assertTrue(report.success)
        self.assertEqual(report.final_output, "Wiki Data Output")
        self.assertEqual(report.steps_taken, 1)
        self.assertAlmostEqual(report.total_duration_ms, 2000.0, delta=100.0)
        self.assertEqual(report.total_tokens, 1200)
        self.assertEqual(report.screenshots, ["screenshot1.png"])
        self.assertEqual(report.extracted_artifacts, ["artifact1.json"])
        
        # Test saving to file
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test_report.json")
            report.save_to_file(out_path)
            
            self.assertTrue(os.path.exists(out_path))
            with open(out_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.assertEqual(data["task_id"], "task_test_123")
            self.assertEqual(data["success"], True)
            self.assertEqual(data["final_output"], "Wiki Data Output")
            self.assertEqual(data["metrics"]["tokens"]["total_tokens"], 1200)
            self.assertEqual(data["artifacts"]["screenshots"], ["screenshot1.png"])
