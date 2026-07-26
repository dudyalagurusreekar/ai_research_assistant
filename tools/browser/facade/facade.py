"""Browser Tool Facade implementing core.interfaces.ITool as an independent platform capability."""

import time
from typing import Any, Dict, Optional
from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata
from core.models.tool_result import ToolResult
from core.models.artifact import Artifact
from tools.browser.driver.base import IBrowserDriver
from tools.browser.driver.playwright_driver import PlaywrightDriver
from tools.browser.executor.engine import BrowserExecutor
from tools.browser.dom.processor import DOMProcessor
from tools.browser.rules.engine import BrowserRuleEngine
from tools.browser.verification.verifier import BrowserActionVerifier
from tools.browser.recovery.engine import BrowserRecoveryEngine
from tools.browser.metrics.tracker import BrowserMetricsTracker


class BrowserToolFacade(ITool):
    """Unified Facade for Browser capability plugging into CapabilityRegistry and SessionOrchestrator."""

    def __init__(
        self,
        driver: Optional[IBrowserDriver] = None,
        headless: bool = True,
    ) -> None:
        self.driver = driver or PlaywrightDriver(headless=headless)
        self.executor = BrowserExecutor(driver=self.driver)
        self.dom_processor = DOMProcessor()
        self.rule_engine = BrowserRuleEngine()
        self.verifier = BrowserActionVerifier()
        self.recovery = BrowserRecoveryEngine()
        self.metrics = BrowserMetricsTracker()

        self._metadata = ToolMetadata(
            name="browser_tool",
            version="3.0.0",
            description="High-performance, low-latency, deterministic browser automation capability.",
            capabilities=["browser", "web", "automation", "scrape", "navigate"],
            parameters_schema={
                "action": "Action to perform (navigate, click, type, scroll, wait, extract_text, download, upload)",
                "url": "Target URL for navigate action",
                "selector": "CSS selector or interactive element index for click/type/wait",
                "text": "Text to type for type action",
            },
            tags=["browser", "automation", "web"],
            is_async=True,
            enabled=True,
        )

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata definition."""
        return self._metadata

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute browser workflow action asynchronously.

        Args:
            parameters: Action parameters dictionary.

        Returns:
            ToolResult containing execution data and generated artifacts.
        """
        start_time = time.time()
        action = parameters.get("action") or parameters.get("sub_action") or "navigate"
        old_dom_hash = self.executor.state.dom_version_hash

        # 1. Enforce rule engine wait strategy
        recommended_wait = self.rule_engine.get_wait_strategy(action)

        # 2. Execute deterministic browser action
        exec_result = await self.executor.execute_action(action, parameters)
        success = exec_result.get("success", True)

        # 3. Retrieve DOM and process via DOMProcessor
        raw_html = await self.driver.get_html()
        processed_dom = self.dom_processor.process(raw_html)
        self.executor.state.dom_version_hash = processed_dom.dom_hash

        # 4. Perform Action Verification
        verification = self.verifier.verify_dom_mutation(old_dom_hash, processed_dom.dom_hash)

        # 5. Record telemetry metrics
        duration_ms = (time.time() - start_time) * 1000.0
        self.metrics.record_action(action, duration_ms, success)

        # 6. Build artifacts
        dom_artifact = Artifact(
            name=f"dom_snapshot_{processed_dom.dom_hash}.txt",
            artifact_type="text",
            content=processed_dom.simplified_text,
            metadata={"dom_hash": processed_dom.dom_hash, "token_count": processed_dom.token_count},
        )

        return ToolResult(
            tool_name=self.metadata.name,
            success=success,
            data={
                "action": action,
                "url": self.executor.state.url,
                "dom_summary": processed_dom.simplified_text,
                "verification": {"passed": verification.passed, "details": verification.details},
                "browser_state": self.executor.state.to_dict(),
            },
            execution_time_ms=round(duration_ms, 2),
            artifacts=[dom_artifact],
        )

    async def close(self) -> None:
        """Close browser resources."""
        await self.driver.close()
