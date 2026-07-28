"""Comprehensive test suite for the Recovery Engine.

Tests error classification, metrics tracking, self-healing strategies,
crashes, network disconnections, and planner feedback.
"""

import pytest
from unittest.mock import MagicMock, patch

from tools.browser.models.response import ActionResult
from tools.browser.recovery.base import RecoveryContext
from tools.browser.recovery.classifier import ErrorCategory, ErrorClassifier
from tools.browser.recovery.engine import RecoveryEngine, RecoveryMetrics, RecoveryPolicyEngine
from tools.browser.recovery.strategies import (
    AlternativeSelectorDiscovery,
    BrowserCrashRecovery,
    DismissOverlay,
    NetworkInterruptionRecovery,
    PlannerFeedbackStrategy,
    RetryWithBackoff,
    ScrollIntoView,
    SessionRefresh,
    WaitForDOMStability,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def mock_browser():
    """Create a mock Browser facade returning realistic ActionResults."""
    browser = MagicMock()
    
    # Successful ActionResult default mock
    action_res = ActionResult(
        url="https://example.com/page",
        title="Example Page",
        success=True,
        data="subaction_ok",
    )
    
    browser.click.return_value = action_res
    browser.open_url.return_value = action_res
    browser.wait_for_selector.return_value = action_res
    browser.wait_for_network_idle.return_value = action_res
    browser.execute_javascript.return_value = ActionResult(
        url="https://example.com/page",
        title="Example Page",
        success=True,
        data="js_result",
    )
    
    browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com/page")
    browser.get_page_title.return_value = MagicMock(success=True, data="Example Page")
    browser.get_page_html.return_value = MagicMock(success=True, data="<html></html>")
    browser.capture_screenshot.return_value = MagicMock(success=True, data=b"screenshot_bytes")
    browser.history = ["https://example.com/page"]
    return browser


@pytest.fixture
def mock_executor(mock_browser):
    """Create a mock BrowserActionExecutor."""
    executor = MagicMock()
    executor.browser = mock_browser
    executor.execute.return_value = ActionResult(
        url="https://example.com/page",
        title="Example Page",
        success=True,
        data="subaction_ok",
    )
    return executor


# ─────────────────────────────────────────────
# Error Classifier Tests
# ─────────────────────────────────────────────

class TestErrorClassifier:
    """Tests for raw message error classification taxonomy."""

    @pytest.mark.parametrize(
        "msg,expected_category",
        [
            ("stale element reference: element is not attached to the page document", ErrorCategory.STALE_ELEMENT),
            ("Unable to locate element with CSS selector: div.main", ErrorCategory.ELEMENT_NOT_FOUND),
            ("element click intercepted by another div element", ErrorCategory.ELEMENT_NOT_INTERACTABLE),
            ("unexpected alert open: dialog active", ErrorCategory.DIALOG_BLOCKING),
            ("SessionExpiredError: your login session has timed out", ErrorCategory.SESSION_EXPIRED),
            ("401 Unauthorized: credentials invalid", ErrorCategory.AUTH_INTERRUPTION),
            ("net::ERR_CONNECTION_REFUSED at url", ErrorCategory.NETWORK_ERROR),
            ("Playwright context destroyed / target page closed", ErrorCategory.BROWSER_CRASH),
            ("Cloudflare verify you are human captcha barrier", ErrorCategory.CAPTCHA_INTERRUPTION),
            ("Navigation timeout of 30000ms exceeded", ErrorCategory.TIMEOUT),
            ("Javascript error: null pointer in script", ErrorCategory.JS_EXCEPTION),
            ("Failed to load url (navigation error)", ErrorCategory.NAVIGATION_FAILURE),
            ("Some completely random and unclassified error message", ErrorCategory.UNKNOWN),
        ]
    )
    def test_classification_matching(self, msg, expected_category):
        """Should classify text patterns into expected taxonomy category."""
        assert ErrorClassifier.classify(msg) == expected_category


# ─────────────────────────────────────────────
# Recovery Metrics Tests
# ─────────────────────────────────────────────

class TestRecoveryMetrics:
    """Tests for the metrics tracker."""

    def test_metrics_accumulation(self):
        """Should accurately summarize success, failure, and execution time stats."""
        metrics = RecoveryMetrics()

        metrics.record_attempt(ErrorCategory.STALE_ELEMENT, "wait_for_dom_stability", True, 250.0, "Success")
        metrics.record_attempt(ErrorCategory.TIMEOUT, "retry_with_backoff", False, 1000.0, "Failed")

        assert metrics.total_attempts == 2
        assert metrics.total_successes == 1
        assert metrics.total_failures == 1
        assert metrics.total_recovery_time_ms == 1250.0

        d = metrics.to_dict()
        assert d["success_rate_pct"] == 50.0
        assert d["avg_recovery_time_ms"] == 625.0
        assert d["by_category"]["STALE_ELEMENT"]["successes"] == 1
        assert d["by_strategy"]["retry_with_backoff"]["failures"] == 1
        assert len(metrics.history) == 2


# ─────────────────────────────────────────────
# Strategy Execution Tests
# ─────────────────────────────────────────────

class TestRecoveryStrategies:
    """Tests for self-healing strategies."""

    def test_retry_with_backoff(self, mock_browser, mock_executor):
        """Should sleep then execute again."""
        ctx = RecoveryContext(
            browser=mock_browser,
            action_dict={"action": "click", "selector": "#btn"},
            failed_result=ActionResult(url="https://a.com", title="", success=False),
            error_category=ErrorCategory.TIMEOUT,
            error_message="timeout",
        )
        strategy = RetryWithBackoff(base_delay_s=0.01, max_delay_s=0.1)
        res = strategy.attempt(ctx)
        
        assert res.success is True
        assert res.strategy_used == "retry_with_backoff"

    def test_wait_for_dom_stability(self, mock_browser, mock_executor):
        """Should wait for network/DOM then execute."""
        ctx = RecoveryContext(
            browser=mock_browser,
            action_dict={"action": "click", "selector": "#btn"},
            failed_result=ActionResult(url="https://a.com", title="", success=False),
            error_category=ErrorCategory.STALE_ELEMENT,
            error_message="stale",
        )
        strategy = WaitForDOMStability()
        res = strategy.attempt(ctx)
        
        assert res.success is True
        mock_browser.wait_for_network_idle.assert_called_once()

    def test_alternative_selector_discovery(self, mock_browser, mock_executor):
        """Should run JS to find selector, and execute with it."""
        mock_browser.execute_javascript.return_value = ActionResult(
            url="https://example.com/page", title="", success=True, data="#new-btn-id"
        )
        # Mock the click action to succeed
        mock_browser.click.return_value = ActionResult(url="https://example.com/page", title="", success=True)
        
        ctx = RecoveryContext(
            browser=mock_browser,
            action_dict={"action": "click", "selector": "button[name='login']"},
            failed_result=ActionResult(url="https://a.com", title="", success=False),
            error_category=ErrorCategory.ELEMENT_NOT_FOUND,
            error_message="not found",
        )
        strategy = AlternativeSelectorDiscovery()
        res = strategy.attempt(ctx)

        assert res.success is True
        assert res.discovered_alternative_selector == "#new-btn-id"
        
        # Verify click was invoked with alternative selector
        mock_browser.click.assert_called_with("#new-btn-id", timeout=None)

    def test_dismiss_overlay(self, mock_browser, mock_executor):
        """Should run JS to close popups, and retry."""
        ctx = RecoveryContext(
            browser=mock_browser,
            action_dict={"action": "click", "selector": "#btn"},
            failed_result=ActionResult(url="https://a.com", title="", success=False),
            error_category=ErrorCategory.ELEMENT_NOT_INTERACTABLE,
            error_message="obscured",
        )
        strategy = DismissOverlay()
        res = strategy.attempt(ctx)
        
        assert res.success is True
        # Verify overlay dismissal JS script was called
        called_scripts = [call[0][0] for call in mock_browser.execute_javascript.call_args_list]
        assert any("overlaySelectors" in s for s in called_scripts)

    def test_scroll_into_view(self, mock_browser, mock_executor):
        """Should run JS scroll, and retry."""
        ctx = RecoveryContext(
            browser=mock_browser,
            action_dict={"action": "click", "selector": "#btn"},
            failed_result=ActionResult(url="https://a.com", title="", success=False),
            error_category=ErrorCategory.ELEMENT_NOT_INTERACTABLE,
            error_message="obscured",
        )
        strategy = ScrollIntoView()
        res = strategy.attempt(ctx)
        
        assert res.success is True
        # Verify specific scroll into view script call
        mock_browser.execute_javascript.assert_any_call(
            "document.querySelector('#btn')?.scrollIntoView({behavior:'instant',block:'center'})"
        )

    def test_session_refresh(self, mock_browser, mock_executor):
        """Should refresh page, and retry."""
        ctx = RecoveryContext(
            browser=mock_browser,
            action_dict={"action": "click", "selector": "#btn"},
            failed_result=ActionResult(url="https://a.com", title="", success=False),
            error_category=ErrorCategory.AUTH_INTERRUPTION,
            error_message="auth",
        )
        strategy = SessionRefresh()
        res = strategy.attempt(ctx)
        
        assert res.success is True
        mock_browser.open_url.assert_called_once_with("https://example.com/page")


# ─────────────────────────────────────────────
# Browser Crash & Session Restoration Simulation
# ─────────────────────────────────────────────

class TestBrowserCrashRecovery:
    """Tests for browser crash spawning recovery."""

    def test_browser_crash_restoration(self, mock_browser, mock_executor):
        """Should tear down, restart browser context, reload page, and retry."""
        ctx = RecoveryContext(
            browser=mock_browser,
            action_dict={"action": "click", "selector": "#btn"},
            failed_result=ActionResult(url="https://crashed-url.com", title="", success=False),
            error_category=ErrorCategory.BROWSER_CRASH,
            error_message="context destroyed",
        )
        
        # Mock class initialization
        mock_automation = MagicMock()
        mock_automation._run_sync.return_value = None
        
        with patch("tools.browser.automation.engine.BrowserAutomationEngine") as MockAuto:
            MockAuto.return_value = mock_automation
            
            strategy = BrowserCrashRecovery()
            res = strategy.attempt(ctx)
            
            assert res.success is True
            assert "recovered from browser crash" in res.message
            
            # Browser reload should be attempted to last known URL
            mock_browser.open_url.assert_called_with("https://example.com/page")


# ─────────────────────────────────────────────
# Network Loss Simulation
# ─────────────────────────────────────────────

class TestNetworkInterruptionRecovery:
    """Tests for network outage recovery."""

    @patch("urllib.request.urlopen")
    def test_network_outage_restored(self, mock_urlopen, mock_browser, mock_executor):
        """Should check ping repeatedly, detect online, reload page, and retry."""
        # First 2 pings raise exception, 3rd succeeds
        call_count = [0]
        def mock_ping(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception("Network unreachable")
            return MagicMock()
        mock_urlopen.side_effect = mock_ping

        ctx = RecoveryContext(
            browser=mock_browser,
            action_dict={"action": "click", "selector": "#btn"},
            failed_result=ActionResult(url="https://site.com", title="", success=False),
            error_category=ErrorCategory.NETWORK_ERROR,
            error_message="net::ERR_CONNECTION_REFUSED",
        )
        
        strategy = NetworkInterruptionRecovery(max_wait_s=5.0)
        res = strategy.attempt(ctx)
        
        assert res.success is True
        assert res.attempts == 3
        mock_browser.open_url.assert_called_once_with("https://example.com/page")

    @patch("urllib.request.urlopen")
    def test_network_outage_timeout(self, mock_urlopen, mock_browser, mock_executor):
        """Should fail if connection remains offline throughout wait budget."""
        mock_urlopen.side_effect = Exception("offline")
        
        ctx = RecoveryContext(
            browser=mock_browser,
            action_dict={"action": "click", "selector": "#btn"},
            failed_result=ActionResult(url="https://site.com", title="", success=False),
            error_category=ErrorCategory.NETWORK_ERROR,
            error_message="net::ERR_CONNECTION_REFUSED",
        )
        
        strategy = NetworkInterruptionRecovery(max_wait_s=0.05)
        res = strategy.attempt(ctx)
        
        assert res.success is False
        assert "remained offline" in res.message


# ─────────────────────────────────────────────
# Planner Feedback Strategy Tests
# ─────────────────────────────────────────────

class TestPlannerFeedback:
    """Tests for planner feedback generation."""

    def test_planner_feedback_packing(self, mock_browser):
        """Should return failure ActionResult populated with natural language feedback."""
        ctx = RecoveryContext(
            browser=mock_browser,
            action_dict={"action": "click", "selector": "input#submit"},
            failed_result=ActionResult(url="https://a.com", title="", success=False, errors=["Timeout"]),
            error_category=ErrorCategory.TIMEOUT,
            error_message="Timeout loading selector input#submit",
        )
        
        strategy = PlannerFeedbackStrategy()
        res = strategy.attempt(ctx)
        
        assert res.success is False
        assert "planner_feedback" in res.action_result.data
        feedback = res.action_result.data["planner_feedback"]
        assert "failed completely with category" in feedback
        assert "input#submit" in feedback


# ─────────────────────────────────────────────
# Recovery Engine Integration Tests
# ─────────────────────────────────────────────

class TestRecoveryEngineIntegration:
    """Tests for the primary RecoveryEngine orchestrator."""

    def test_recovery_chain_exhaustion(self, mock_browser, mock_executor):
        """Should run through strategies and run the planner feedback fallback if all fail."""
        # Fail all click actions directly on browser mock
        mock_browser.click.return_value = ActionResult(
            url="https://example.com/page", title="", success=False, errors=["Timeout"]
        )

        engine = RecoveryEngine(mock_browser, max_recovery_attempts=2)
        
        # Override policies for ELEMENT_NOT_FOUND to retry twice
        policy_engine = RecoveryPolicyEngine()
        policy_engine.set_policy(ErrorCategory.ELEMENT_NOT_FOUND, [
            RetryWithBackoff(0.01, 0.02),
            RetryWithBackoff(0.01, 0.02),
        ])
        engine.policy_engine = policy_engine

        failed_res = ActionResult(url="https://example.com", title="", success=False, errors=["Element not found"])
        res = engine.attempt_recovery(
            action_dict={"action": "click", "selector": "#btn"},
            failed_result=failed_res,
        )

        assert res.success is False
        # Verifies PlannerFeedbackStrategy was run as final fallback
        assert "planner_feedback" in res.action_result.data
        assert res.attempts == 2

    def test_recovery_success(self, mock_browser, mock_executor):
        """Should run strategy chain and return success on first successful recovery."""
        # First click fails, second click succeeds
        mock_browser.click.side_effect = [
            ActionResult(url="https://example.com/page", title="", success=False, errors=["Not found"]),
            ActionResult(url="https://example.com/page", title="", success=True, data="recovered!"),
        ]

        engine = RecoveryEngine(mock_browser)
        policy_engine = RecoveryPolicyEngine()
        policy_engine.set_policy(ErrorCategory.ELEMENT_NOT_FOUND, [
            WaitForDOMStability(),
            AlternativeSelectorDiscovery(),
        ])
        engine.policy_engine = policy_engine

        failed_res = ActionResult(url="https://example.com", title="", success=False, errors=["Element not found"])
        res = engine.attempt_recovery(
            action_dict={"action": "click", "selector": "#btn"},
            failed_result=failed_res,
        )

        assert res.success is True
        assert res.attempts == 2  # Succeeded on 2nd strategy (AlternativeSelectorDiscovery)
        assert res.action_result.data == "recovered!"
