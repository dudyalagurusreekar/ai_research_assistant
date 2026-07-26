"""Comprehensive test suite for the Completion Detector.

Tests individual completion strategies, aggregation logic, blocker overrides,
and production-ready scenarios.
"""

import pytest
from unittest.mock import MagicMock

from tools.browser.models.response import ActionResult
from tools.browser.detector.base import (
    CompletionContext,
    CompletionState,
    CompletionStatus,
    InvalidObjectiveError,
)
from tools.browser.detector.pipeline import CompletionDetector
from tools.browser.detector.strategies import (
    ArtifactSuccessStrategy,
    ExecutionAnomalyStrategy,
    ObjectiveEvidenceStrategy,
    StateBlockedStrategy,
    UrlRedirectionStrategy,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def mock_browser():
    """Create a mock Browser facade for evaluating strategies."""
    browser = MagicMock()
    browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com/dashboard")
    browser.get_clean_text.return_value = MagicMock(success=True, data="Welcome to the dashboard! Order confirmed successfully.")
    return browser


# ─────────────────────────────────────────────
# Individual Strategies Unit Tests
# ─────────────────────────────────────────────

class TestStrategies:
    """Unit tests for individual completion detection strategies."""

    def test_objective_evidence_strategy_success(self, mock_browser):
        """Should detect success when key words in objective match page content."""
        ctx = CompletionContext(
            objective="Confirm the order on the dashboard.",
            browser=mock_browser
        )
        strategy = ObjectiveEvidenceStrategy()
        res = strategy.evaluate(ctx)

        assert res.state == CompletionState.COMPLETED
        assert res.confidence >= 0.7
        assert any("dashboard" in ev for ev in res.evidence)

    def test_objective_evidence_strategy_incomplete(self, mock_browser):
        """Should return incomplete when keywords don't match."""
        mock_browser.get_clean_text.return_value = MagicMock(success=True, data="Empty blank landing page.")
        ctx = CompletionContext(
            objective="Download the quarterly profit invoice report PDF",
            browser=mock_browser
        )
        strategy = ObjectiveEvidenceStrategy()
        res = strategy.evaluate(ctx)

        assert res.state == CompletionState.INCOMPLETE
        assert res.confidence == 0.0

    def test_artifact_success_strategy_download(self, mock_browser):
        """Should verify completion if downloads or exported files are registered."""
        strategy = ArtifactSuccessStrategy()

        # Context has downloaded file
        ctx = CompletionContext(
            objective="Download the invoice PDF.",
            browser=mock_browser,
            extracted_artifacts={"downloaded_files": ["invoice_102.pdf"]}
        )
        res = strategy.evaluate(ctx)
        assert res.state == CompletionState.COMPLETED
        assert res.confidence == 1.0

        # Context has download action in history
        ctx_history = CompletionContext(
            objective="Download the report spreadsheet.",
            browser=mock_browser,
            history=[{"action": "download_file", "success": True}]
        )
        res_history = strategy.evaluate(ctx_history)
        assert res_history.state == CompletionState.COMPLETED
        assert res_history.confidence == 0.9

    def test_artifact_success_strategy_extraction(self, mock_browser):
        """Should verify completion if data extraction variables exist."""
        ctx = CompletionContext(
            objective="Scrape the listed search results.",
            browser=mock_browser,
            extracted_artifacts={"scraped_data": [{"title": "Item 1", "price": "$10"}]}
        )
        strategy = ArtifactSuccessStrategy()
        res = strategy.evaluate(ctx)

        assert res.state == CompletionState.COMPLETED
        assert res.confidence == 1.0
        assert "target dataset" in res.explanation.lower()

    def test_url_redirection_strategy(self, mock_browser):
        """Should recognize success paths in the URL."""
        strategy = UrlRedirectionStrategy()

        # Set URL to success path matching objective
        mock_browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com/checkout")
        ctx_success = CompletionContext(objective="Checkout items", browser=mock_browser)
        res_success = strategy.evaluate(ctx_success)
        assert res_success.state == CompletionState.COMPLETED
        assert "checkout" in res_success.explanation

        # Non-matching URL
        mock_browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com/search?q=test")
        ctx_fail = CompletionContext(objective="Checkout items", browser=mock_browser)
        res_fail = strategy.evaluate(ctx_fail)
        assert res_fail.state == CompletionState.INCOMPLETE

    def test_state_blocked_strategy_captcha(self, mock_browser):
        """Should detect CAPTCHA security screens."""
        mock_browser.get_clean_text.return_value = MagicMock(
            success=True, data="Please verify you are human. Complete the Cloudflare captcha below."
        )
        ctx = CompletionContext(objective="Find documents", browser=mock_browser)
        strategy = StateBlockedStrategy()
        res = strategy.evaluate(ctx)

        assert res.state == CompletionState.BLOCKED
        assert "captcha" in res.explanation.lower()

    def test_state_blocked_strategy_auth_gate(self, mock_browser):
        """Should flag login redirection if objective is not auth related."""
        mock_browser.get_current_url.return_value = MagicMock(success=True, data="https://site.com/login?redirect=/admin")
        mock_browser.get_clean_text.return_value = MagicMock(success=True, data="Please sign in to proceed.")
        
        # Scenario A: Objective is not auth
        ctx = CompletionContext(objective="Search for products on dashboard", browser=mock_browser)
        strategy = StateBlockedStrategy()
        res = strategy.evaluate(ctx)
        assert res.state == CompletionState.BLOCKED
        assert "login or authentication" in res.explanation.lower()

        # Scenario B: Objective is login
        ctx_login = CompletionContext(objective="Login to your profile page", browser=mock_browser)
        res_login = strategy.evaluate(ctx_login)
        assert res_login.state == CompletionState.INCOMPLETE  # Not blocked, this is what we wanted!

    def test_state_blocked_strategy_server_error(self, mock_browser):
        """Should detect 404 or 500 error pages."""
        mock_browser.get_clean_text.return_value = MagicMock(success=True, data="404 Not Found - Server Error")
        ctx = CompletionContext(objective="Scrape text", browser=mock_browser)
        strategy = StateBlockedStrategy()
        res = strategy.evaluate(ctx)

        assert res.state == CompletionState.IMPOSSIBLE
        assert "404" in res.explanation

    def test_execution_anomaly_strategy_loops(self, mock_browser):
        """Should detect infinite loop cycles in history action paths."""
        history = [
            {"action": "click", "selector": "#next", "url": "https://a.com", "success": True},
            {"action": "click", "selector": "#next", "url": "https://a.com", "success": True},
            {"action": "click", "selector": "#next", "url": "https://a.com", "success": True},
            {"action": "click", "selector": "#next", "url": "https://a.com", "success": True},
            {"action": "click", "selector": "#next", "url": "https://a.com", "success": True},
            {"action": "click", "selector": "#next", "url": "https://a.com", "success": True},
        ]
        ctx = CompletionContext(objective="Scrape lists", browser=mock_browser, history=history)
        strategy = ExecutionAnomalyStrategy()
        res = strategy.evaluate(ctx)

        assert res.state == CompletionState.IMPOSSIBLE
        assert "infinite loop" in res.explanation.lower()

    def test_execution_anomaly_strategy_consecutive_failures(self, mock_browser):
        """Should flag impossibility if action steps fail repeatedly."""
        history = [{"action": "click", "success": False}] * 5
        ctx = CompletionContext(objective="Submit form", browser=mock_browser, history=history)
        strategy = ExecutionAnomalyStrategy()
        res = strategy.evaluate(ctx)

        assert res.state == CompletionState.IMPOSSIBLE
        assert "failed 5 actions consecutively" in res.explanation.lower()


# ─────────────────────────────────────────────
# Main Pipeline Integration & Scenario Tests
# ─────────────────────────────────────────────

class TestCompletionDetectorPipeline:
    """Scenarios and pipeline aggregation tests."""

    def test_validation_input_objectives(self, mock_browser):
        """Should raise error on empty goals."""
        detector = CompletionDetector(mock_browser)
        with pytest.raises(InvalidObjectiveError):
            detector.evaluate_completion("", [])

    def test_scenario_successful_completion(self, mock_browser):
        """Pipeline returns COMPLETED if weighted score is high."""
        detector = CompletionDetector(mock_browser)
        
        # High keyword match + success URL redirect
        res = detector.evaluate_completion(
            objective="Confirm the dashboard checkout order.",
            history=[]
        )

        assert res.state == CompletionState.COMPLETED
        assert res.confidence >= 0.50

    def test_scenario_uncertain_completion(self, mock_browser):
        """Pipeline returns UNCERTAIN if signals are moderately positive."""
        # Moderate match, no success redirect or download
        mock_browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com/other")
        mock_browser.get_clean_text.return_value = MagicMock(success=True, data="Confirm details.")
        
        detector = CompletionDetector(mock_browser)
        res = detector.evaluate_completion(
            objective="Confirm dashboard checkout order",
            history=[]
        )

        assert res.state == CompletionState.UNCERTAIN
        assert 0.10 <= res.confidence < 0.85

    def test_scenario_false_positive_prevention(self, mock_browser):
        """Pipeline flags incomplete if URL/keywords match is too low."""
        mock_browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com/home")
        mock_browser.get_clean_text.return_value = MagicMock(success=True, data="Login page or generic footer text.")
        
        detector = CompletionDetector(mock_browser)
        res = detector.evaluate_completion(
            objective="Download the quarterly invoice spreadsheet",
            history=[]
        )

        assert res.state == CompletionState.INCOMPLETE
        assert res.confidence < 0.40

    def test_scenario_blocked_override(self, mock_browser):
        """Hard override block triggers immediately despite other success parameters."""
        mock_browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com/checkout")
        # Captcha exists on checkout page
        mock_browser.get_clean_text.return_value = MagicMock(success=True, data="Welcome checkout! Complete security captcha verification.")
        
        detector = CompletionDetector(mock_browser)
        res = detector.evaluate_completion(
            objective="Checkout items on dashboard",
            history=[]
        )

        assert res.state == CompletionState.BLOCKED
        assert "captcha" in res.explanation.lower()

    def test_scenario_impossible_override(self, mock_browser):
        """Repeated errors immediately override other parameters to report impossible."""
        mock_browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com/success")
        mock_browser.get_clean_text.return_value = MagicMock(success=True, data="Thank you for your order!")
        
        # But we have consecutive failures (e.g. elements not interactable or missing target variables)
        history = [{"action": "click", "success": False}] * 6
        
        detector = CompletionDetector(mock_browser)
        res = detector.evaluate_completion(
            objective="Confirm order placement and download receipt PDF",
            history=history
        )

        assert res.state == CompletionState.IMPOSSIBLE
        assert "consecutively" in res.explanation.lower()
