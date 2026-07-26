"""Comprehensive test suite for the Macro Action Engine component.

Tests macro registration, execution, nested macros, parameter validation,
error classification, retry policies, and rollback strategies.
"""

import json
import time
import pytest
from unittest.mock import MagicMock, patch

from tools.browser.macro.base import (
    BaseMacro,
    MacroExecutionContext,
    MacroExecutionError,
    MacroRollbackError,
    MacroValidationError,
    global_registry,
    register_macro,
)
from tools.browser.macro.engine import MacroActionEngine
from tools.browser.models.response import ActionResult, ActionMetrics


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def mock_browser():
    """Create a mock Browser facade."""
    browser = MagicMock()
    browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com")
    browser.get_page_title.return_value = MagicMock(success=True, data="Example Page")
    browser.get_page_html.return_value = MagicMock(success=True, data="<html></html>")
    browser.capture_screenshot.return_value = MagicMock(success=True, data=b"screenshot_bytes")
    browser.execute_javascript.return_value = MagicMock(success=True, data="js_result")
    return browser


@pytest.fixture
def mock_executor(mock_browser):
    """Create a mock BrowserActionExecutor."""
    executor = MagicMock()
    executor.browser = mock_browser
    
    # Setup state manager mock
    state_manager = MagicMock()
    state_manager.capture_state.return_value = {"snapshot_id": "test_snap"}
    state_manager.restore_state.return_value = True
    executor.state_manager = state_manager
    
    # Default sub-action execute behavior
    executor.execute.return_value = ActionResult(
        url="https://example.com",
        title="Example",
        success=True,
        data="subaction_data",
    )
    
    return executor


@pytest.fixture
def engine(mock_executor):
    """Create a MacroActionEngine."""
    return MacroActionEngine(mock_executor)


# ─────────────────────────────────────────────
# Registry & Custom Macro Tests
# ─────────────────────────────────────────────

class TestMacroRegistry:
    """Tests for the macro registry mechanism."""

    def test_custom_macro_registration(self):
        """Should register a custom macro and list it."""
        @register_macro("macro_test_dummy")
        class DummyMacro(BaseMacro):
            @property
            def name(self) -> str:
                return "macro_test_dummy"
            @property
            def description(self) -> str:
                return "A dummy test macro."
            def validate(self, params):
                pass
            def execute(self, params):
                return ActionResult(url="about:blank", title="", success=True)

        assert global_registry.get("macro_test_dummy") is DummyMacro
        assert "macro_test_dummy" in global_registry.list_macros()
        assert global_registry.list_macros()["macro_test_dummy"] == "A dummy test macro."


# ─────────────────────────────────────────────
# Execution Context & Tracing
# ─────────────────────────────────────────────

class TestExecutionContext:
    """Tests for the MacroExecutionContext."""

    def test_context_recording(self, mock_executor):
        """Context should capture and log sub-action steps."""
        context = MacroExecutionContext(mock_executor, {})
        context.record_step("open_url", True, 150.0)
        context.record_step("click", False, 50.0, "Element not found")

        assert len(context.trace) == 2
        assert context.trace[0]["action"] == "open_url"
        assert context.trace[0]["success"] is True
        assert context.trace[1]["action"] == "click"
        assert context.trace[1]["success"] is False
        assert context.trace[1]["error"] == "Element not found"

    def test_checkpoint_lifecycle(self, mock_executor):
        """Context should save and restore checkpoints."""
        context = MacroExecutionContext(mock_executor, {})
        
        # Save checkpoint
        cp_id = context.create_checkpoint()
        assert cp_id != ""
        assert cp_id in context.checkpoints
        mock_executor.state_manager.capture_state.assert_called_once()

        # Restore checkpoint
        success = context.restore_checkpoint(cp_id)
        assert success is True
        mock_executor.state_manager.restore_state.assert_called_once_with({"snapshot_id": "test_snap"})


# ─────────────────────────────────────────────
# Engine Execution & Validation
# ─────────────────────────────────────────────

class TestMacroEngineExecution:
    """Tests for parameter validation and rollback strategies."""

    def test_invalid_macro_name(self, engine):
        """Running an unregistered macro should fail gracefully."""
        res = engine.run_macro("macro_nonexistent", {})
        assert res.success is False
        assert "Unknown macro action" in res.errors[0]

    def test_parameter_validation_failure(self, engine):
        """Failing parameter validation should return ActionResult with validation error."""
        # SearchMacro requires 'text_input'
        res = engine.run_macro("macro_search", {})
        assert res.success is False
        assert "validation failed" in res.errors[0]

    def test_rollback_on_failure(self, engine, mock_executor):
        """Failing macro steps should trigger rollback checkpoint restoration."""
        # Mock executor to return success at first, then fail
        call_count = [0]
        def mock_exec_sub(action):
            call_count[0] += 1
            if call_count[0] == 1:
                return ActionResult(url="https://a.com", title="A", success=True)
            return ActionResult(url="https://a.com", title="A", success=False, errors=["Selector error"])
        
        mock_executor.execute.side_effect = mock_exec_sub

        res = engine.run_macro("macro_search", {"text_input": "cats"})
        assert res.success is False
        
        # Checkpoint restoration should have been attempted
        mock_executor.state_manager.restore_state.assert_called_once()

    def test_retry_policy(self, engine, mock_executor):
        """Macro should retry on failure if retry_limit is configured."""
        call_count = [0]
        def mock_exec_sub(action):
            call_count[0] += 1
            if call_count[0] <= 3:  # Fail first 3 sub-actions
                return ActionResult(url="https://fail.com", title="Fail", success=False, errors=["Network error"])
            return ActionResult(url="https://success.com", title="Success", success=True, data="Ok")
            
        mock_executor.execute.side_effect = mock_exec_sub

        # Run with 2 retries (total 3 attempts) -> Should still fail
        res = engine.run_macro("macro_search", {"text_input": "dogs", "retry_limit": 2, "retry_delay": 0.01})
        assert res.success is False
        assert res.metrics.retries_attempted == 2

        # Run with 3 retries (total 4 attempts) -> Should succeed
        call_count[0] = 0
        res = engine.run_macro("macro_search", {"text_input": "dogs", "retry_limit": 3, "retry_delay": 0.01})
        assert res.success is True
        assert res.metrics.retries_attempted <= 3


# ─────────────────────────────────────────────
# Built-in Macros Individual Tests
# ─────────────────────────────────────────────

class TestBuiltinMacros:
    """Detailed tests for each of the core built-in macros."""

    def test_search_macro_external(self, engine, mock_executor):
        """Should execute Google search sub-actions and return result."""
        res = engine.run_macro("macro_search", {"text_input": "ai agents", "search_scope": "external"})
        assert res.success is True
        
        # External search (Google) involves: open_url, wait_for_network_idle, get_clean_text
        actions_run = [call[0][0]["action"] for call in mock_executor.execute.call_args_list]
        assert "open_url" in actions_run
        assert "wait_for_network_idle" in actions_run
        assert "get_clean_text" in actions_run

    def test_search_macro_current_site(self, engine, mock_executor):
        """Should execute fill_input on current site and return result."""
        res = engine.run_macro("macro_search", {"text_input": "ai agents", "search_scope": "current_site"})
        assert res.success is True
        
        # Current site search involves: wait_for_selector, fill_input, wait_for_network_idle, get_clean_text
        actions_run = [call[0][0]["action"] for call in mock_executor.execute.call_args_list]
        assert "wait_for_selector" in actions_run
        assert "fill_input" in actions_run
        assert "wait_for_network_idle" in actions_run
        assert "get_clean_text" in actions_run

    def test_login_macro(self, engine, mock_executor):
        """Should execute login form fills and submit."""
        credentials = {"#username": "admin", "#password": "secret"}
        res = engine.run_macro("macro_login", {
            "url": "https://auth.com",
            "credentials": credentials,
            "selector": "#login-btn"
        })
        assert res.success is True

        actions_run = [call[0][0]["action"] for call in mock_executor.execute.call_args_list]
        assert "open_url" in actions_run
        assert actions_run.count("fill_input") == 2
        assert "click" in actions_run

    def test_form_filling_macro(self, engine, mock_executor):
        """Should execute multi-field form fills."""
        form_data = {"#first_name": "John", "#last_name": "Doe"}
        res = engine.run_macro("macro_fill_form", {
            "form_data": form_data,
            "selector": "#submit-btn"
        })
        assert res.success is True

        actions_run = [call[0][0]["action"] for call in mock_executor.execute.call_args_list]
        assert actions_run.count("fill_input") == 2
        assert "click" in actions_run

    def test_article_extraction_macro(self, engine, mock_executor):
        """Should navigate and read article content."""
        res = engine.run_macro("macro_extract_article", {"url": "https://news.com/agent-operators"})
        assert res.success is True
        
        actions_run = [call[0][0]["action"] for call in mock_executor.execute.call_args_list]
        assert actions_run == ["open_url", "get_clean_text"]

    def test_page_capture_macro(self, engine, mock_executor):
        """Should capture page screenshot, logs, and network in one run."""
        res = engine.run_macro("macro_capture_page", {"url": "https://dashboard.com"})
        assert res.success is True
        
        actions_run = [call[0][0]["action"] for call in mock_executor.execute.call_args_list]
        assert "capture_screenshot" in actions_run
        assert "capture_network_requests" in actions_run
        assert "capture_console_logs" in actions_run

    def test_scrape_macro(self, engine, mock_executor):
        """Should extract matching elements using javascript execution."""
        mock_executor.execute.return_value = ActionResult(
            url="https://scrape.com", title="", success=True, data=["Product 1", "Product 2"]
        )

        res = engine.run_macro("macro_scrape", {"selector": ".product-title", "url": "https://scrape.com"})
        assert res.success is True
        assert res.data == ["Product 1", "Product 2"]

        actions_run = [call[0][0]["action"] for call in mock_executor.execute.call_args_list]
        assert "open_url" in actions_run
        assert "execute_javascript" in actions_run

    def test_comparison_macro(self, engine, mock_executor):
        """Should open two URLs and return similarity metrics."""
        call_count = [0]
        def mock_exec_sub(action):
            call_count[0] += 1
            if call_count[0] == 2:  # Page 1 clean text
                return ActionResult(url="https://url1.com", title="", success=True, data="Hello world")
            if call_count[0] == 4:  # Page 2 clean text
                return ActionResult(url="https://url2.com", title="", success=True, data="Hello agents")
            return ActionResult(url="https://example.com", title="", success=True)
            
        mock_executor.execute.side_effect = mock_exec_sub

        res = engine.run_macro("macro_compare", {"url": "https://url1.com", "other_url": "https://url2.com"})
        assert res.success is True
        assert res.data["url1_length"] == 11
        assert res.data["url2_length"] == 12
        assert res.data["text_length_similarity_pct"] > 90.0

    def test_file_upload_macro(self, engine, mock_executor):
        """Should trigger file upload."""
        res = engine.run_macro("macro_upload_file", {
            "selector": "input[type='file']",
            "file_path": "d:/documents/resume.pdf",
        })
        assert res.success is True
        
        actions_run = [call[0][0]["action"] for call in mock_executor.execute.call_args_list]
        assert "upload_file" in actions_run

    def test_file_download_macro(self, engine, mock_executor):
        """Should trigger file download."""
        res = engine.run_macro("macro_download_file", {
            "selector": "a#download-zip",
            "download_dir": "d:/downloads",
        })
        assert res.success is True
        
        actions_run = [call[0][0]["action"] for call in mock_executor.execute.call_args_list]
        assert "download_file" in actions_run


# ─────────────────────────────────────────────
# Nested Macro Composition
# ─────────────────────────────────────────────

class TestNestedMacroComposition:
    """Tests composition of macros calling other macros."""

    def test_nested_macro_execution(self, engine, mock_executor):
        """Should execute a macro that delegates to sub-macros."""
        # Let's register a composite macro that calls macro_search, then macro_extract_article
        @register_macro("macro_search_and_summarize")
        class CompositeMacro(BaseMacro):
            @property
            def name(self) -> str:
                return "macro_search_and_summarize"
            @property
            def description(self) -> str:
                return "Search Google, then extract the article."
            def validate(self, params):
                if "query" not in params:
                    raise MacroValidationError("query is required")
            def execute(self, params):
                # 1. Run Search Macro nested
                search_res = self.run_sub_action({
                    "action": "macro_search",
                    "text_input": params["query"]
                })
                # 2. Run Extract Article nested on result domain / mock URL
                article_res = self.run_sub_action({
                    "action": "macro_extract_article",
                    "url": "https://mockarticle.com/page"
                })
                return article_res

        # Set up mock executor to recognize and delegate macro_ actions using the engine
        def mock_exec_routing(action_dict):
            act = action_dict.get("action")
            if act.startswith("macro_"):
                # Forward back to the engine!
                return engine.run_macro(act, action_dict)
            return ActionResult(url="https://example.com", title="", success=True, data="sub_ok")

        mock_executor.execute.side_effect = mock_exec_routing

        res = engine.run_macro("macro_search_and_summarize", {"query": "deep learning"})
        assert res.success is True
        
        # Verify trace contains step items from nested macro runs
        trace = res.verification["macro_trace"]
        assert trace[0]["action"] == "macro_search"
        assert trace[1]["action"] == "macro_extract_article"
