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
from tools.browser.platform.engine import BrowserPlatformEngine


class BrowserToolFacade(ITool):
    """Unified Facade for Browser capability plugging into CapabilityRegistry and SessionOrchestrator."""

    name = "browser_tool"

    def __init__(
        self,
        driver: Optional[IBrowserDriver] = None,
        headless: bool = True,
        browser: Optional[Any] = None,
    ) -> None:
        self.name = "browser_tool"
        self.browser = browser
        self.driver = driver or (browser.driver if browser and hasattr(browser, "driver") else PlaywrightDriver(headless=headless))
        self.executor = BrowserExecutor(driver=self.driver)
        self.dom_processor = DOMProcessor()
        self.rule_engine = BrowserRuleEngine()
        self.verifier = BrowserActionVerifier()
        self.recovery = BrowserRecoveryEngine()
        self.metrics = BrowserMetricsTracker()
        self.platform_engine = BrowserPlatformEngine()

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

    def forward(self, action: str, **kwargs) -> str:
        """Synchronous execution method compatibility wrapper for smolagents and tests."""
        import json
        import asyncio
        params = {"action": action, **kwargs}
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                res = pool.submit(asyncio.run, self.execute(params)).result()
        else:
            res = loop.run_until_complete(self.execute(params))

        if hasattr(res, "to_dict"):
            d = res.to_dict()
            if "data" in d and isinstance(d["data"], dict):
                for k, v in d["data"].items():
                    if k not in d:
                        d[k] = v
            return json.dumps(d)
        elif hasattr(res, "content"):
            return json.dumps({"content": res.content, "success": getattr(res, "success", True)})
        return json.dumps({"result": str(res)})

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute browser workflow action asynchronously.

        Args:
            parameters: Action parameters dictionary.

        Returns:
            ToolResult containing execution data and generated artifacts.
        """
        start_time = time.time()
        action = parameters.get("action") or parameters.get("sub_action") or "navigate"

        if self.browser:
            if action in ("open_url", "navigate") and hasattr(self.browser, "open_url"):
                url_arg = parameters.get("url") or parameters.get("target_url") or "about:blank"
                res = self.browser.open_url(url_arg)
                res_dict = res.to_dict() if hasattr(res, "to_dict") else (res if isinstance(res, dict) else {"url": url_arg, "success": True})
                return ToolResult(tool_name=self.name, success=getattr(res, "success", True), data=res_dict)
            elif hasattr(self.browser, "execute_action"):
                try:
                    from tools.browser.constants import BrowserAction
                    from tools.browser.models.request import ActionParams
                    act_str = parameters.get("action") or "open_url"
                    try:
                        action_enum = BrowserAction(act_str.upper())
                    except ValueError:
                        try:
                            action_enum = BrowserAction(act_str.lower())
                        except ValueError:
                            action_enum = BrowserAction.OPEN_URL
                    extra = {k: v for k, v in parameters.items() if k not in ("action", "selector", "text", "text_input")}
                    action_obj = ActionParams(
                        action=action_enum,
                        selector=parameters.get("selector"),
                        text_input=parameters.get("text") or parameters.get("text_input"),
                        extra_args=extra,
                    )
                except Exception:
                    action_obj = parameters
                try:
                    res = self.browser.execute_action(action_obj)
                    res_dict = res.to_dict() if hasattr(res, "to_dict") else (res if isinstance(res, dict) else {"url": parameters.get("url", ""), "success": True})
                    return ToolResult(tool_name=self.name, success=getattr(res, "success", True), data=res_dict)
                except Exception as exc:
                    err_msg = f"Action parameter validation error: selector is required ({exc})"
                    return ToolResult(tool_name=self.name, success=False, error_message=err_msg, data={"success": False, "errors": [err_msg], "url": parameters.get("url", "")})

        old_dom_hash = self.executor.state.dom_version_hash

        # 1. Enforce rule engine wait strategy
        self.rule_engine.get_wait_strategy(action)

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
