"""Unit tests for Sprint 11 Browser Automation Platform."""

import pytest
import asyncio
from tools.browser.platform.models import (
    BrowserConfig,
    SessionConfig,
    BrowserAction,
    ActionType,
    WaitStrategy,
    ExtractionSchema,
    WorkflowStep,
    WorkflowDefinition,
)
from tools.browser.platform.browser_manager import BrowserManager
from tools.browser.platform.session_manager import SessionManager
from tools.browser.platform.navigation_engine import NavigationEngine
from tools.browser.platform.dom_engine import DOMUnderstandingEngine
from tools.browser.platform.interaction_engine import InteractionEngine
from tools.browser.platform.extraction_engine import ExtractionEngine
from tools.browser.platform.auth_manager import AuthenticationManager
from tools.browser.platform.download_manager import DownloadManager
from tools.browser.platform.upload_manager import UploadManager
from tools.browser.platform.screenshot_manager import ScreenshotManager
from tools.browser.platform.captcha_detector import CaptchaDetector
from tools.browser.platform.workflow_recorder import WorkflowRecorder
from tools.browser.platform.workflow_executor import WorkflowExecutor
from tools.browser.platform.error_recovery import ErrorRecoveryEngine
from tools.browser.platform.security_layer import SecurityLayer
from tools.browser.platform.metrics import BrowserMetricsEngine
from tools.browser.platform.engine import BrowserPlatformEngine


def test_browser_manager_lifecycle():
    async def _test():
        config = BrowserConfig(headless=True, browser_type="chromium")
        manager = BrowserManager(config)
        
        assert await manager.initialize() is True
        assert manager.is_active is True
        
        ctx = await manager.create_context("test_ctx")
        assert ctx is not None
        assert "test_ctx" in manager._contexts
        
        health = await manager.check_health()
        assert health["active"] is True
        
        assert await manager.close_context("test_ctx") is True
        await manager.shutdown()
        assert manager.is_active is False

    asyncio.run(_test())


def test_session_manager_persistence(tmp_path):
    session_mgr = SessionManager(storage_dir=str(tmp_path))
    session = session_mgr.create_session("sess_001", cookies=[{"name": "test_cookie", "value": "123"}])
    
    assert session.session_id == "sess_001"
    assert len(session.cookies) == 1
    
    # Save session
    assert asyncio.run(session_mgr.save_session("sess_001")) is True
    
    # Load session
    loaded = session_mgr.load_session("sess_001")
    assert loaded is not None
    assert loaded.session_id == "sess_001"
    assert loaded.cookies[0]["name"] == "test_cookie"
    
    # Delete session
    assert session_mgr.delete_session("sess_001") is True


def test_navigation_engine_mock_mode():
    async def _test():
        nav_engine = NavigationEngine(retries=1)
        
        class DummyPage:
            url = "about:blank"
        
        page = DummyPage()
        res = await nav_engine.navigate(page, "https://example.com")
        
        assert res.success is True
        assert res.action_type == ActionType.NAVIGATE
        assert res.url == "https://example.com"

    asyncio.run(_test())


def test_dom_understanding_engine():
    dom_engine = DOMUnderstandingEngine()
    sample_html = """
    <html>
      <head><title>Test Page</title></head>
      <body>
        <h1 id="header">Welcome</h1>
        <button id="btn-submit" type="submit">Submit Form</button>
        <a href="/login" class="nav-link">Login</a>
      </body>
    </html>
    """
    
    tree = dom_engine.parse_html_to_dom_tree(sample_html, url="https://example.com", title="Test Page")
    
    assert tree.title == "Test Page"
    assert tree.total_nodes > 0
    assert len(tree.interactive_elements) == 2
    
    llm_prompt = dom_engine.format_interactive_elements_for_llm(tree)
    assert "Submit Form" in llm_prompt
    assert "btn-submit" in llm_prompt


def test_interaction_engine_actions():
    async def _test():
        interaction = InteractionEngine(humanize_delay_ms=0)
        
        class DummyPage:
            url = "https://example.com"
            
            async def click(self, selector, **kwargs):
                pass
            
            async def fill(self, selector, text, **kwargs):
                pass

        page = DummyPage()
        
        # Click action
        click_act = BrowserAction(action_type=ActionType.CLICK, target_selector="#btn-submit")
        click_res = await interaction.execute_action(page, click_act)
        assert click_res.success is True
        
        # Type action
        type_act = BrowserAction(action_type=ActionType.TYPE, target_selector="input[name='q']", text="ARA Sprint 11")
        type_res = await interaction.execute_action(page, type_act)
        assert type_res.success is True

    asyncio.run(_test())


def test_extraction_engine():
    async def _test():
        extractor = ExtractionEngine()
        sample_html = """
        <html>
          <body>
            <div class="product">
              <h2 class="title">Product A</h2>
              <span class="price">$19.99</span>
            </div>
            <div class="product">
              <h2 class="title">Product B</h2>
              <span class="price">$29.99</span>
            </div>
          </body>
        </html>
        """
        
        class DummyPage:
            async def content(self):
                return sample_html

        page = DummyPage()
        
        schema = ExtractionSchema(
            schema_id="products_schema",
            name="Products",
            container_selector=".product",
            multiple=True,
            fields={"title": ".title", "price": ".price"},
        )
        
        res = await extractor.extract_schema(page, schema)
        assert res.success is True
        assert res.item_count == 2
        assert res.extracted_data[0]["title"] == "Product A"
        assert res.extracted_data[1]["price"] == "$29.99"

    asyncio.run(_test())


def test_captcha_detector():
    async def _test():
        detector = CaptchaDetector()
        
        class DummyCaptchaPage:
            async def content(self):
                return "<html><body><div class='g-recaptcha' data-sitekey='xxx'></div></body></html>"
                
        class DummyNormalPage:
            async def content(self):
                return "<html><body><h1>Welcome to ARA</h1></body></html>"

        captcha_res = await detector.detect_captcha(DummyCaptchaPage())
        assert captcha_res.captcha_detected is True
        assert captcha_res.provider == "recaptcha"
        
        normal_res = await detector.detect_captcha(DummyNormalPage())
        assert normal_res.captcha_detected is False

    asyncio.run(_test())


def test_security_layer_guardrails():
    security = SecurityLayer()
    
    # Normal safe action
    safe_act = BrowserAction(action_type=ActionType.NAVIGATE, url="https://example.com")
    safe_assessment = security.assess_action_safety(safe_act)
    assert safe_assessment.is_safe is True
    assert safe_assessment.is_high_impact is False
    
    # High-impact destructive action
    high_impact_act = BrowserAction(
        action_type=ActionType.CLICK,
        target_selector="button#delete-all-account-data",
        text="Delete Account Data Permanently",
    )
    hi_assessment = security.assess_action_safety(high_impact_act)
    assert hi_assessment.is_high_impact is True
    assert hi_assessment.requires_user_confirmation is True
    
    # Default policy blocks without explicit user callback
    assert security.request_user_confirmation(high_impact_act, hi_assessment) is False


def test_workflow_recorder_and_executor(tmp_path):
    async def _test():
        recorder = WorkflowRecorder(storage_dir=str(tmp_path))
        recorder.start_recording("wf_001", "Sample Search Workflow")
        
        act1 = BrowserAction(action_type=ActionType.NAVIGATE, url="https://example.com")
        act2 = BrowserAction(action_type=ActionType.TYPE, target_selector="input[name='q']", text="{query}")
        
        recorder.record_step(act1, "Navigate to homepage")
        recorder.record_step(act2, "Type search query")
        
        wf = recorder.stop_recording()
        assert wf is not None
        assert len(wf.steps) == 2
        
        loaded_wf = recorder.load_workflow("wf_001")
        assert loaded_wf is not None
        assert loaded_wf.name == "Sample Search Workflow"

        class DummyPage:
            url = "about:blank"
            async def goto(self, url, **kwargs): pass
            async def fill(self, selector, text, **kwargs): pass

        executor = WorkflowExecutor()
        exec_res = await executor.execute_workflow(DummyPage(), loaded_wf, parameters={"query": "AI Research"})
        assert exec_res.success is True
        assert len(exec_res.step_results) == 2

    asyncio.run(_test())


def test_browser_platform_engine_end_to_end():
    async def _test():
        engine = BrowserPlatformEngine()
        
        # Initialize
        assert await engine.initialize() is True
        
        # Navigate
        nav_res = await engine.navigate("https://example.com")
        assert nav_res.success is True
        
        # Extract DOM Tree
        dom_tree = await engine.get_dom_tree()
        assert dom_tree is not None
        
        # Metrics check
        summary = engine.metrics_engine.get_summary()
        assert summary["total_actions"] >= 1
        assert summary["success_rate_pct"] == 100.0
        
        await engine.shutdown()

    asyncio.run(_test())
