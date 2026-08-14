"""Master Platform Engine for Sprint 11 Browser Automation Platform."""

import logging
import time
from typing import Any, Dict, List, Optional, Union
from tools.browser.platform.auth_manager import AuthenticationManager
from tools.browser.platform.browser_manager import BrowserManager
from tools.browser.platform.captcha_detector import CaptchaDetector
from tools.browser.platform.dom_engine import DOMUnderstandingEngine
from tools.browser.platform.download_manager import DownloadManager
from tools.browser.platform.error_recovery import ErrorRecoveryEngine
from tools.browser.platform.extraction_engine import ExtractionEngine
from tools.browser.platform.interaction_engine import InteractionEngine
from tools.browser.platform.metrics import BrowserMetricsEngine
from tools.browser.platform.models import (
    ActionResult,
    ActionType,
    BrowserAction,
    BrowserConfig,
    DOMTree,
    ExtractionResult,
    ExtractionSchema,
    WaitStrategy,
    WorkflowDefinition,
    WorkflowExecutionResult,
)
from tools.browser.platform.navigation_engine import NavigationEngine
from tools.browser.platform.screenshot_manager import ScreenshotManager
from tools.browser.platform.security_layer import SecurityLayer
from tools.browser.platform.session_manager import SessionManager
from tools.browser.platform.upload_manager import UploadManager
from tools.browser.platform.workflow_executor import WorkflowExecutor
from tools.browser.platform.workflow_recorder import WorkflowRecorder

logger = logging.getLogger("Tools.Browser.Platform.BrowserPlatformEngine")


class BrowserPlatformEngine:
    """Production-grade Browser Automation Platform Engine for ARA."""

    def __init__(
        self,
        config: Optional[BrowserConfig] = None,
        security_layer: Optional[SecurityLayer] = None,
    ) -> None:
        self.config = config or BrowserConfig()
        self.browser_manager = BrowserManager(config=self.config)
        self.session_manager = SessionManager()
        self.navigation_engine = NavigationEngine()
        self.dom_engine = DOMUnderstandingEngine()
        self.interaction_engine = InteractionEngine()
        self.extraction_engine = ExtractionEngine()
        self.auth_manager = AuthenticationManager()
        self.download_manager = DownloadManager()
        self.upload_manager = UploadManager()
        self.screenshot_manager = ScreenshotManager()
        self.captcha_detector = CaptchaDetector()
        self.workflow_recorder = WorkflowRecorder()
        self.workflow_executor = WorkflowExecutor(
            navigation_engine=self.navigation_engine,
            interaction_engine=self.interaction_engine,
        )
        self.error_recovery = ErrorRecoveryEngine()
        self.security_layer = security_layer or SecurityLayer()
        self.metrics_engine = BrowserMetricsEngine()

        self._active_page = None
        self._active_context = None
        self._active_session_id = "default"

    async def initialize(self) -> bool:
        """Initialize browser manager and default context/page."""
        success = await self.browser_manager.initialize()
        if success:
            self._active_context = await self.browser_manager.create_context(self._active_session_id)
            if hasattr(self._active_context, "pages") and self._active_context.pages:
                self._active_page = self._active_context.pages[0]
            elif hasattr(self._active_context, "new_page"):
                self._active_page = await self._active_context.new_page()
            self.metrics_engine.set_active_contexts(len(self.browser_manager._contexts))
        return success

    async def navigate(
        self,
        url: str,
        wait_strategy: WaitStrategy = WaitStrategy.NETWORK_IDLE,
        timeout_ms: int = 30000,
    ) -> ActionResult:
        """Navigate to URL with security check, CAPTCHA scan, and metrics recording."""
        await self.initialize()

        action = BrowserAction(
            action_type=ActionType.NAVIGATE,
            url=url,
            wait_strategy=wait_strategy,
            timeout_ms=timeout_ms,
        )

        # Security check
        assessment = self.security_layer.assess_action_safety(action)
        if not assessment.is_safe:
            self.metrics_engine.record_security_interception()
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                message="Navigation blocked by security layer.",
                url=url,
                error="; ".join(assessment.reasons),
            )

        # Navigation execution
        result = await self.navigation_engine.navigate(
            self._active_page, url, wait_strategy=wait_strategy, timeout_ms=timeout_ms
        )

        # CAPTCHA detection scan
        captcha_res = await self.captcha_detector.detect_captcha(self._active_page)
        if captcha_res.captcha_detected:
            self.metrics_engine.record_captcha_detected()
            result.success = False
            result.message = f"CAPTCHA detected ({captcha_res.provider}). Automated bypass is prohibited."
            result.error = captcha_res.details

        self.metrics_engine.record_action(result)
        return result

    async def execute_action(self, action: BrowserAction) -> ActionResult:
        """Execute a browser action with safety checks, error recovery, and metrics recording."""
        await self.initialize()

        # Security check
        assessment = self.security_layer.assess_action_safety(action, target_url=getattr(self._active_page, "url", ""))
        if assessment.requires_user_confirmation:
            approved = self.security_layer.request_user_confirmation(action, assessment)
            if not approved:
                self.metrics_engine.record_security_interception()
                return ActionResult(
                    success=False,
                    action_type=action.action_type,
                    message="Action blocked: User confirmation rejected or required.",
                    error="; ".join(assessment.reasons),
                )

        if action.action_type == ActionType.NAVIGATE:
            return await self.navigate(action.url or "about:blank", action.wait_strategy, action.timeout_ms)

        # Execute interaction with error recovery
        async def _run():
            return await self.interaction_engine.execute_action(self._active_page, action)

        result = await self.error_recovery.execute_with_fallback(_run, self._active_page)

        # CAPTCHA check
        captcha_res = await self.captcha_detector.detect_captcha(self._active_page)
        if captcha_res.captcha_detected:
            self.metrics_engine.record_captcha_detected()
            result.success = False
            result.message = f"CAPTCHA detected ({captcha_res.provider}). Automated bypass is prohibited."
            result.error = captcha_res.details

        self.metrics_engine.record_action(result)
        return result

    async def get_dom_tree(self) -> DOMTree:
        """Get structured DOMTree from active page."""
        await self.initialize()
        return await self.dom_engine.build_dom_tree(self._active_page)

    async def extract_text(self, selector: Optional[str] = None) -> str:
        """Extract clean text content from active page."""
        await self.initialize()
        return await self.extraction_engine.extract_text(self._active_page, selector=selector)

    async def extract_schema(self, schema: ExtractionSchema) -> ExtractionResult:
        """Extract structured data using ExtractionSchema."""
        await self.initialize()
        return await self.extraction_engine.extract_schema(self._active_page, schema)

    async def capture_screenshot(self, full_page: bool = False, selector: Optional[str] = None) -> ActionResult:
        """Capture screenshot of active page."""
        await self.initialize()
        res = await self.screenshot_manager.capture_screenshot(self._active_page, full_page=full_page, selector=selector)
        self.metrics_engine.record_action(res)
        return res

    async def execute_workflow(
        self, workflow: WorkflowDefinition, parameters: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecutionResult:
        """Execute a recorded workflow definition."""
        await self.initialize()
        return await self.workflow_executor.execute_workflow(self._active_page, workflow, parameters)

    async def shutdown(self) -> None:
        """Shutdown platform engine and clean up resources."""
        await self.browser_manager.shutdown()
        self._active_page = None
        self._active_context = None
        logger.info("BrowserPlatformEngine shutdown complete.")
