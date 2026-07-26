"""Comprehensive test suite for the Loop Detector.

Tests page fingerprinters, graph transition cycles, valid polling filters,
and escape recovery suggestions.
"""

import pytest
from unittest.mock import MagicMock

from tools.browser.detector import CompletionState
from tools.browser.loop.base import LoopDetectionResult, LoopType
from tools.browser.loop.detector import LoopDetector
from tools.browser.loop.fingerprint import BrowserStateFingerprinter


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def mock_browser():
    """Create a mock Browser facade."""
    browser = MagicMock()
    browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com/item")
    browser.get_page_title.return_value = MagicMock(success=True, data="Product Page")
    browser.get_clean_text.return_value = MagicMock(success=True, data="No loading message present.")
    
    # Mock JS execute to return static DOM counts
    browser.execute_javascript.return_value = MagicMock(
        success=True,
        data='{"elementCount": 100, "scrollX": 0, "scrollY": 0}'
    )
    return browser


# ─────────────────────────────────────────────
# Browser State Fingerprinter Tests
# ─────────────────────────────────────────────

class TestBrowserStateFingerprinter:
    """Tests for the layout state hash generation."""

    def test_fingerprint_generation_is_stable(self, mock_browser):
        """Identical page configurations should generate the identical hash signature."""
        h1 = BrowserStateFingerprinter.get_fingerprint(mock_browser)
        h2 = BrowserStateFingerprinter.get_fingerprint(mock_browser)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 length

    def test_fingerprint_changes_on_scroll(self, mock_browser):
        """Scrolling coordinates updates should change the hash output."""
        h1 = BrowserStateFingerprinter.get_fingerprint(mock_browser)

        # Update scroll coordinates
        mock_browser.execute_javascript.return_value = MagicMock(
            success=True,
            data='{"elementCount": 100, "scrollX": 0, "scrollY": 500}'
        )
        h2 = BrowserStateFingerprinter.get_fingerprint(mock_browser)

        assert h1 != h2

    def test_fingerprint_changes_on_url(self, mock_browser):
        """Navigating to a different URL should change the hash output."""
        h1 = BrowserStateFingerprinter.get_fingerprint(mock_browser)
        mock_browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com/checkout")
        h2 = BrowserStateFingerprinter.get_fingerprint(mock_browser)

        assert h1 != h2


# ─────────────────────────────────────────────
# Loop Detector Engine Tests
# ─────────────────────────────────────────────

class TestLoopDetectorEngine:
    """Tests for the LoopDetector orchestrator."""

    def test_no_loop_on_fresh_history(self, mock_browser):
        """Should report no loop on short history traces."""
        detector = LoopDetector(mock_browser)
        res = detector.check_loop()
        assert res.loop_detected is False
        assert "short" in res.explanation

    def test_action_loop_detection_cycle_1(self, mock_browser):
        """Should detect repeated single-action cycles (e.g. click, click, click)."""
        detector = LoopDetector(mock_browser)

        # Record identical click action 3 times
        action = {"action": "click", "selector": "button#submit", "text_input": None}
        for _ in range(3):
            detector.record_step(action, "https://example.com/home")

        res = detector.check_loop()
        assert res.loop_detected is True
        assert res.loop_type == LoopType.ACTION
        assert res.cycle_length == 1
        assert res.recommended_escape == "skip"

    def test_action_loop_detection_cycle_2(self, mock_browser):
        """Should detect repeating multi-action sequences (e.g. click -> type -> click -> type)."""
        detector = LoopDetector(mock_browser)

        step_a = {"action": "click", "selector": "#open-modal", "text_input": None}
        step_b = {"action": "type_text", "selector": "#name-field", "text_input": "user"}

        # Repeat step_a and step_b sequence twice
        for _ in range(2):
            detector.record_step(step_a, "https://example.com/form")
            detector.record_step(step_b, "https://example.com/form")

        res = detector.check_loop()
        assert res.loop_detected is True
        assert res.loop_type == LoopType.ACTION
        assert res.cycle_length == 2
        assert res.recommended_escape == "skip"

    def test_navigation_loop_detection(self, mock_browser):
        """Should detect back-and-forth URL navigation cycles (e.g. URL A -> B -> A -> B)."""
        detector = LoopDetector(mock_browser)
    
        # Alternate selector/action params to prevent triggering ACTION loop first
        urls = ["https://a.com", "https://b.com", "https://a.com", "https://b.com", "https://a.com", "https://b.com"]
        
        for idx, url in enumerate(urls):
            action = {"action": "click", "selector": f"a.nav-{idx}"}
            mock_browser.get_current_url.return_value = MagicMock(success=True, data=url)
            detector.record_step(action, url)
    
        res = detector.check_loop()
        assert res.loop_detected is True
        assert res.loop_type == LoopType.NAVIGATION
        assert res.cycle_length == 2
        assert res.recommended_escape == "rollback"

    def test_state_oscillation_detection(self, mock_browser):
        """Should detect cycles in layout states (oscillating DOM layout structures)."""
        detector = LoopDetector(mock_browser)
    
        # Generate hashes dynamically matching layouts A and B
        layouts = [
            '{"elementCount": 100, "scrollX": 0, "scrollY": 0}',
            '{"elementCount": 200, "scrollX": 0, "scrollY": 0}',
            '{"elementCount": 100, "scrollX": 0, "scrollY": 0}',
            '{"elementCount": 200, "scrollX": 0, "scrollY": 0}',
            '{"elementCount": 100, "scrollX": 0, "scrollY": 0}',
            '{"elementCount": 200, "scrollX": 0, "scrollY": 0}',
        ]
        
        for idx, layout in enumerate(layouts):
            action = {"action": "click", "selector": f"#toggle-{idx}"}
            mock_browser.execute_javascript.return_value = MagicMock(success=True, data=layout)
            detector.record_step(action, "https://example.com/dashboard")
    
        res = detector.check_loop()
        assert res.loop_detected is True
        assert res.loop_type == LoopType.STATE
        assert res.cycle_length == 2
        assert res.recommended_escape == "replan"

    def test_recovery_loop_detection(self, mock_browser):
        """Should detect repeated failed self-healing recovery actions."""
        detector = LoopDetector(mock_browser)

        action = {"action": "click", "selector": "#broken-btn"}
        # Record same recovery strategy on same selector 3 times
        for _ in range(3):
            detector.record_step(action, "https://site.com", recovery_strategy="dismiss_overlay")

        res = detector.check_loop()
        assert res.loop_detected is True
        assert res.loop_type == LoopType.RECOVERY
        assert res.recommended_escape == "terminate"

    def test_planner_loop_detection(self, mock_browser):
        """Should detect repeating reasoning patterns from the planner."""
        detector = LoopDetector(mock_browser)
        thought = "Selecting product category and confirming layout options."
    
        for idx in range(4):
            action = {"action": "click", "selector": f"#btn-{idx}"}
            detector.record_step(action, "https://site.com", thought=thought)
    
        res = detector.check_loop()
        assert res.loop_detected is True
        assert res.loop_type == LoopType.PLANNER
        assert res.recommended_escape == "replan"

    def test_valid_polling_filter(self, mock_browser):
        """Should not flag repeated actions if they match status checking or waiting."""
        detector = LoopDetector(mock_browser)

        # Polling action check
        poll_action = {"action": "click", "selector": "span#loading-spinner", "text_input": "check status"}
        
        # Simulate loading text on page content
        mock_browser.get_clean_text.return_value = MagicMock(success=True, data="Status: Loading... Please wait.")

        for _ in range(4):
            detector.record_step(poll_action, "https://example.com/job-status")

        res = detector.check_loop()
        assert res.loop_detected is False
        assert "polling" in res.explanation
