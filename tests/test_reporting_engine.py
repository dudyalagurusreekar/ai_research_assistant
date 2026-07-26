"""Comprehensive test suite for the Reporting Engine.

Tests event logging, recovery statistics aggregation, artifact indexing,
budget snapshot integration, and JSON/Markdown/HTML report exports.
"""

import json
import time

from tools.browser.budget import BudgetLimit, BudgetManager, ResourceCategory
from tools.browser.reporting.base import ReportFormat, ReportMetadata
from tools.browser.reporting.engine import ReportingEngine


class TestReportingEngine:
    """Tests for the ReportingEngine coordinator."""

    def test_log_event_aggregates_timeline(self):
        """Should record timeline events and aggregate recovery counts."""
        engine = ReportingEngine()
        
        # 1. Log a planning event
        engine.log_event(1, "planning", "Planner decided to search for item.")
        
        # 2. Log a successful recovery event
        engine.log_event(
            step_number=2,
            category="recovery",
            message="Recovered from element missing error.",
            metadata={"strategy": "discover_selector", "success": True}
        )

        assert len(engine.timeline) == 2
        assert engine.timeline[0].category == "PLANNING"
        
        # Verify recovery statistics accumulation
        stats = engine.recovery_statistics
        assert stats["attempts"] == 1
        assert stats["successes"] == 1
        assert stats["failures"] == 0
        assert stats["strategies_triggered"]["discover_selector"] == 1

    def test_record_artifact(self):
        """Should index artifacts with data value and epoch timestamps."""
        engine = ReportingEngine()
        engine.record_artifact("downloaded_pdf", "/path/to/invoice.pdf", {"size_bytes": 1024})

        assert "downloaded_pdf" in engine.artifacts
        art = engine.artifacts["downloaded_pdf"]
        assert art["value"] == "/path/to/invoice.pdf"
        assert art["details"]["size_bytes"] == 1024
        assert art["timestamp"] > 0.0

    def test_generate_report_with_budget(self):
        """Should gather timelines and compile report data with budget snapshots."""
        engine = ReportingEngine()
        engine.log_event(1, "action", "Clicked search button.")
        engine.record_artifact("query_result", "Item found")

        # Set up a budget manager
        budget = BudgetManager()
        budget.consume(ResourceCategory.ACTIONS, 5)

        meta = ReportMetadata(
            objective="Find invoices",
            status="COMPLETED",
            duration_seconds=12.5,
            start_time=time.time() - 12.5,
            end_time=time.time(),
            confidence=0.95
        )

        report = engine.generate_report(meta, budget_manager=budget)
        
        assert report.metadata.objective == "Find invoices"
        assert len(report.timeline) == 1
        assert "query_result" in report.artifacts
        
        # Budget check
        assert "ACTIONS" in report.budget_utilization
        actions_budget = report.budget_utilization["ACTIONS"]
        assert actions_budget["consumed"] == 5.0
        assert actions_budget["limit"] == 25.0

    def test_export_formats(self):
        """Should compile JSON, Markdown, and HTML report layouts correctly."""
        engine = ReportingEngine()
        engine.log_event(1, "action", "Clicked first tab.")
        engine.record_artifact("tab_title", "Home Page")

        budget = BudgetManager()
        budget.consume(ResourceCategory.ACTIONS, 2)

        meta = ReportMetadata(
            objective="Verify navigation tabs",
            status="COMPLETED",
            duration_seconds=5.0,
            start_time=time.time() - 5.0,
            end_time=time.time(),
            confidence=1.0
        )

        report = engine.generate_report(meta, budget_manager=budget)

        # 1. JSON Export
        json_report = engine.export_report(report, ReportFormat.JSON)
        parsed = json.loads(json_report)
        assert parsed["metadata"]["objective"] == "Verify navigation tabs"
        assert parsed["artifacts"]["tab_title"]["value"] == "Home Page"
        assert len(parsed["timeline"]) == 1

        # 2. Markdown Export
        md_report = engine.export_report(report, ReportFormat.MARKDOWN)
        assert "# Browser Execution Report" in md_report
        assert "**Objective**:" in md_report
        assert "| ACTIONS |" in md_report
        assert "Clicked first tab." in md_report

        # 3. HTML Export
        html_report = engine.export_report(report, ReportFormat.HTML)
        assert "<!DOCTYPE html>" in html_report
        assert "Verify navigation tabs" in html_report
        assert "ACTIONS" in html_report
        assert "Clicked first tab." in html_report
        assert "progress-bar" in html_report
