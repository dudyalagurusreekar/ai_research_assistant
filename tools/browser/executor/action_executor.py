"""Browser Action Executor Middleware.

Exposes a single execution entrypoint representing the middleware between
the LLM Planner/Tool wrapper and the low-level Browser API.
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List

from tools.browser.core.browser import Browser
from tools.browser.models.response import ActionResult, ActionMetrics
from tools.browser.exceptions import ValidationError, BrowserError
from tools.browser.automation.commands import validate_selector_syntax

logger = logging.getLogger("BrowserActionExecutor")


class BrowserActionExecutor:
    """Middleware executor orchestrating browser operations through a unified pipeline."""

    def __init__(self, browser: Browser) -> None:
        """Initialize the executor middleware.

        Args:
            browser (Browser): The Browser facade instance.
        """
        self.browser = browser
        self._logger = logger
        self.history: List[Dict[str, Any]] = []
        from tools.browser.state_manager import BrowserStateMemoryManager
        self.state_manager = BrowserStateMemoryManager(browser)
        from tools.browser.recovery import RecoveryEngine
        self._recovery_engine = RecoveryEngine(browser)
        from tools.browser.memory.manager import MemoryManager
        self.memory_manager = MemoryManager()

        # Lazily-initialized subsystems (set externally or on first use)
        self._tab_coordinator = None
        self._vision_pipeline = None

    def _detect_bot_blocking(self, url: str, title: str, text: str) -> bool:
        """Detect if the current page is a CAPTCHA or bot blocking page."""
        url_lower = url.lower()
        title_lower = title.lower()
        text_lower = (text or "").lower()

        # Google "Sorry" page or generic recaptcha patterns
        if "sorry" in title_lower and "google" in title_lower and "unusual traffic" in text_lower:
            return True
        if "verify you are human" in text_lower or "please complete the security check" in text_lower:
            return True
        if "checking your browser before accessing" in text_lower:
            return True
        if "cloudflare" in text_lower and "attention required" in title_lower:
            return True
        if "captcha" in title_lower or "robot" in title_lower:
            if "verify" in text_lower or "suspicious" in text_lower:
                return True
        return False

    def execute(self, action_dict: Dict[str, Any]) -> ActionResult:
        """Execute a high-level action dictionary through the unified pipeline.

        Args:
            action_dict (Dict[str, Any]): Dictionary describing the action parameters.

        Returns:
            ActionResult: Standardized action result.
        """
        start_time = time.time()
        
        # 1. Parse and Normalize Inputs
        action_name = action_dict.get("action")
        if not action_name:
            return ActionResult(
                url="about:blank",
                title="",
                success=False,
                errors=["Action name is required in action_dict."],
            )
        
        action_lower = action_name.strip().lower()
        
        # Route high-level macro actions to the MacroActionEngine
        if action_lower.startswith("macro_"):
            from tools.browser.macro_engine import MacroActionEngine
            macro_engine = MacroActionEngine(self)
            return macro_engine.run_macro(action_lower, action_dict)

        selector = action_dict.get("selector")
        text_input = action_dict.get("text_input") or action_dict.get("text")
        url = action_dict.get("url")
        key = action_dict.get("key")
        checked = action_dict.get("checked")
        scroll_direction = action_dict.get("scroll_direction")
        scroll_amount = action_dict.get("scroll_amount")
        extra_args = action_dict.get("extra_args")
        timeout = action_dict.get("timeout")
        
        # Map values to appropriate types
        if scroll_amount is not None:
            try:
                scroll_amount = int(scroll_amount)
            except (ValueError, TypeError):
                scroll_amount = 500
        else:
            scroll_amount = 500

        if checked is not None:
            checked = bool(checked)
        else:
            checked = True

        self._logger.info(f"Executor received action '{action_lower}' with selector='{selector}', url='{url}'")

        # 2. Selector Validation
        selector_actions = {
            "click", "double_click", "hover", "fill_input", "type_text",
            "clear_input", "press_key", "select_dropdown", "check_checkbox",
            "upload_file", "download_file", "submit_form", "wait_for_selector"
        }
        
        if action_lower in selector_actions:
            if not selector:
                return ActionResult(
                    url="about:blank",
                    title="",
                    success=False,
                    errors=[f"Action '{action_lower}' selector is required."],
                )
            try:
                validate_selector_syntax(selector)
            except ValidationError as ve:
                self._logger.error(f"Selector validation failed for action '{action_lower}': {ve}")
                return ActionResult(
                    url="about:blank",
                    title="",
                    success=False,
                    errors=[f"Selector validation failed: {ve}"],
                )

        # 3. Pre-Execution Browser State Check
        pre_url = "about:blank"
        pre_title = ""
        try:
            url_res = self.browser.get_current_url()
            pre_url = url_res.data if url_res.success else "about:blank"
            title_res = self.browser.get_page_title()
            pre_title = title_res.data if title_res.success else ""
        except Exception:
            pass

        # 4. Route and Execute Action with Pipeline Error Recovery
        res = None
        err_msg = ""
        try:
            if action_lower == "open_url":
                target_url = url or text_input
                if not target_url:
                    raise ValidationError("Action 'open_url' URL is required.")
                res = self.browser.open_url(target_url, timeout=timeout)
            elif action_lower == "click":
                res = self.browser.click(selector, timeout=timeout)
            elif action_lower == "double_click":
                res = self.browser.double_click(selector, timeout=timeout)
            elif action_lower == "hover":
                res = self.browser.hover(selector, timeout=timeout)
            elif action_lower == "fill_input":
                if text_input is None:
                    raise ValidationError("Action 'fill_input' text_input is required.")
                res = self.browser.fill_input(selector, text_input, timeout=timeout)
            elif action_lower == "type_text":
                if text_input is None:
                    raise ValidationError("Action 'type_text' text_input is required.")
                res = self.browser.type_text(selector, text_input, clear_first=checked, timeout=timeout)
            elif action_lower == "clear_input":
                res = self.browser.clear_input(selector, timeout=timeout)
            elif action_lower == "press_key":
                if not key:
                    raise ValidationError("Action 'press_key' key is required.")
                res = self.browser.press_key(selector, key, timeout=timeout)
            elif action_lower == "select_dropdown":
                if text_input is None:
                    raise ValidationError("Action 'select_dropdown' text_input is required.")
                res = self.browser.select_dropdown(selector, text_input, timeout=timeout)
            elif action_lower == "check_checkbox":
                res = self.browser.check_checkbox(selector, checked=checked, timeout=timeout)
            elif action_lower == "upload_file":
                if not text_input:
                    raise ValidationError("Action 'upload_file' file path is required in text_input.")
                res = self.browser.upload_file(selector, text_input, timeout=timeout)
            elif action_lower == "download_file":
                res = self.browser.download_file(selector, download_dir=text_input, timeout=timeout)
            elif action_lower in ("submit_form", "submit"):
                res = self.browser.submit_form(selector, timeout=timeout)
            elif action_lower == "wait_for_selector":
                res = self.browser.wait_for_selector(selector, state=text_input or "visible", timeout=timeout)
            elif action_lower == "wait_for_navigation":
                res = self.browser.wait_for_navigation(wait_until=text_input, timeout=timeout)
            elif action_lower == "wait_for_function":
                if not extra_args:
                    raise ValidationError("Action 'wait_for_function' extra_args JS statement is required.")
                res = self.browser.wait_for_function(extra_args, arg=text_input, timeout=timeout)
            elif action_lower == "wait_for_url":
                target_url = url or text_input
                if not target_url:
                    raise ValidationError("Action 'wait_for_url' requires target pattern in url or text_input.")
                res = self.browser.wait_for_url(target_url, timeout=timeout)
            elif action_lower == "wait_for_network_idle":
                res = self.browser.wait_for_network_idle(timeout=timeout)
            elif action_lower == "scroll_page":
                res = self.browser.scroll_page(
                    direction=scroll_direction or "down",
                    selector=selector,
                    amount=scroll_amount
                )
            elif action_lower == "execute_javascript":
                if not extra_args:
                    raise ValidationError("Action 'execute_javascript' requires javascript snippet in extra_args.")
                res = self.browser.execute_javascript(extra_args, arg=text_input)
            elif action_lower == "capture_screenshot":
                res = self.browser.capture_screenshot(
                    path=url,
                    full_page=bool(checked),
                    selector=selector,
                )
            elif action_lower == "capture_network_requests":
                res = self.browser.capture_network_requests()
            elif action_lower == "capture_console_logs":
                res = self.browser.capture_console_logs()
            elif action_lower == "get_current_url":
                res = self.browser.get_current_url()
            elif action_lower == "get_page_title":
                target_url = url or text_input
                if target_url and ("://" in target_url or target_url.startswith("about:") or target_url.startswith("data:")):
                    self._logger.info(f"Auto-navigating to '{target_url}' before get_page_title")
                    self.browser.open_url(target_url, timeout=timeout)
                res = self.browser.get_page_title()
            elif action_lower == "get_page_html":
                target_url = url or text_input
                if target_url and ("://" in target_url or target_url.startswith("about:") or target_url.startswith("data:")):
                    self._logger.info(f"Auto-navigating to '{target_url}' before get_page_html")
                    self.browser.open_url(target_url, timeout=timeout)
                res = self.browser.get_page_html()
            elif action_lower == "get_clean_text":
                target_url = url or text_input
                if target_url and ("://" in target_url or target_url.startswith("about:") or target_url.startswith("data:")):
                    self._logger.info(f"Auto-navigating to '{target_url}' before get_clean_text")
                    self.browser.open_url(target_url, timeout=timeout)
                res = self.browser.get_clean_text()
            # ── Tab Management Actions ──
            elif action_lower == "new_tab":
                tab_url = url or text_input or "about:blank"
                coordinator = self._get_tab_coordinator()
                tab_info = coordinator.open_tab(tab_url)
                res = ActionResult(
                    url=tab_info.url, title=tab_info.title, success=True,
                    data={"tab_id": tab_info.tab_id, "url": tab_info.url},
                )
            elif action_lower == "close_tab":
                tab_id = text_input or extra_args
                if not tab_id:
                    raise ValidationError("Action 'close_tab' requires tab_id in text_input.")
                coordinator = self._get_tab_coordinator()
                closed = coordinator.close_tab(tab_id)
                res = ActionResult(
                    url=post_url, title=post_title, success=closed,
                    data={"closed_tab_id": tab_id},
                )
            elif action_lower == "switch_tab":
                tab_id = text_input or extra_args
                if not tab_id:
                    raise ValidationError("Action 'switch_tab' requires tab_id in text_input.")
                coordinator = self._get_tab_coordinator()
                tab_info = coordinator.switch_to_tab(tab_id, navigate_url=url)
                res = ActionResult(
                    url=tab_info.url, title=tab_info.title, success=True,
                    data={"tab_id": tab_info.tab_id},
                )
            elif action_lower == "list_tabs":
                coordinator = self._get_tab_coordinator()
                tabs = coordinator.list_tabs()
                res = ActionResult(
                    url=post_url, title=post_title, success=True,
                    data={"tabs": [t.to_dict() for t in tabs], "count": len(tabs)},
                )
            # ── Vision Actions ──
            elif action_lower == "screenshot_annotated":
                pipeline = self._get_vision_pipeline()
                capture, elements = pipeline.capture_and_annotate()
                res = ActionResult(
                    url=capture.page_url, title=capture.page_title, success=True,
                    data={
                        "file_path": capture.file_path,
                        "elements_count": len(elements),
                        "elements": [e.to_dict() for e in elements[:20]],
                    },
                )
            elif action_lower == "visual_state":
                pipeline = self._get_vision_pipeline()
                state = pipeline.get_visual_state_summary()
                res = ActionResult(
                    url=state.get("page_url", ""), title=state.get("page_title", ""),
                    success=True, data=state,
                )
            else:
                raise ValidationError(f"Unknown browser action: '{action_lower}'")

        except Exception as e:
            self._logger.error(f"Executor encountered exception running '{action_lower}': {e}")
            err_msg = str(e)

        # 5. Post-Execution State Synchronization & Navigation Detection
        
        # FIX: Avoid race conditions by waiting for potential navigation triggered by mutating actions
        mutating_actions = {"click", "double_click", "submit_form", "submit", "press_key"}
        if action_lower in mutating_actions:
            try:
                # Give it a short window to detect a navigation
                self.browser.wait_for_navigation(wait_until="commit", timeout=2.0)
            except Exception:
                pass # Expected if the action did not trigger a navigation

        post_url = pre_url
        post_title = pre_title
        post_text = ""
        try:
            url_res = self.browser.get_current_url()
            post_url = url_res.data if url_res.success else pre_url
            title_res = self.browser.get_page_title()
            post_title = title_res.data if title_res.success else pre_title
            text_res = self.browser.get_clean_text()
            post_text = text_res.data if text_res.success else ""
        except Exception:
            pass

        # Parse final ActionResult
        if res is None:
            duration_ms = (time.time() - start_time) * 1000.0
            res = ActionResult(
                url=post_url,
                title=post_title,
                success=False,
                errors=[err_msg or f"Action '{action_lower}' failed without returning ActionResult."],
                metrics=ActionMetrics(
                    execution_time_ms=duration_ms,
                    retries_attempted=0,
                )
            )

        # 5.2 Detect Bot Blocking
        if res.success and self._detect_bot_blocking(post_url, post_title, post_text):
            res.success = False
            err_msg = "BlockedState: Bot protection or CAPTCHA detected."
            res.errors.append(err_msg)
            from tools.browser.exceptions import BrowserError
            # This specific string helps the RecoveryEngine classify it as CAPTCHA_INTERRUPTION
            self._logger.warning(err_msg)

        # 5.5 Action Verification
        if res.success:
            verification_data = {}
            if pre_url != post_url:
                verification_data["navigation_occurred"] = True
                verification_data["new_url"] = post_url
            
            mutating_actions = {"click", "double_click", "submit_form", "press_key", "hover"}
            input_actions = {"fill_input", "type_text", "clear_input", "select_dropdown", "check_checkbox", "upload_file"}
            
            if action_lower in mutating_actions:
                verification_data["interaction_success"] = True
            elif action_lower in input_actions:
                verification_data["input_success"] = True
                if text_input is not None:
                    verification_data["field_value"] = text_input
                if action_lower == "check_checkbox":
                    verification_data["checked_state"] = checked
                
            if verification_data:
                if res.verification:
                    res.verification.update(verification_data)
                else:
                    res.verification = verification_data

        # 6. Attempt Self-Healing Recovery on failure
        if not res.success and self._recovery_engine is not None:
            try:
                recovery_result = self._recovery_engine.attempt_recovery(
                    action_dict=action_dict,
                    failed_result=res,
                    memory_manager=getattr(self, 'memory_manager', None)
                )
                if recovery_result.success and recovery_result.action_result:
                    self._logger.info(
                        f"Recovery succeeded via '{recovery_result.strategy_used}' "
                        f"after {recovery_result.attempts} attempt(s)"
                    )
                    res = recovery_result.action_result
            except Exception as re_err:
                self._logger.warning(f"Recovery engine error (non-fatal): {re_err}")

        # Record executor history
        self.history.append({
            "action": action_lower,
            "selector": selector,
            "url": url,
            "success": res.success,
            "pre_url": pre_url,
            "post_url": post_url,
            "timestamp": time.time(),
        })

        # Capture memory state snapshot automatically
        try:
            self.state_manager.capture_state(action_dict)
        except Exception as se:
            self._logger.warning(f"State capture skipped/failed during action execution: {se}")

        # Log to agent memory
        if hasattr(self, 'memory_manager') and self.memory_manager is not None:
            # Add to working memory recent steps
            error_msg = " ".join(res.errors) if res.errors else ""
            self.memory_manager.working.log_step(action_dict, res.success, error_msg)
            # Add to long-term episodic memory
            self.memory_manager.episodic.log_execution(
                action=action_lower,
                selector=selector,
                success=res.success,
                error=error_msg
            )

        return res

    def _get_tab_coordinator(self):
        """Lazy-initialize and return the MultiTabCoordinator.

        Returns:
            MultiTabCoordinator: The tab management coordinator.
        """
        if self._tab_coordinator is None:
            from tools.browser.tabs.coordinator import MultiTabCoordinator
            self._tab_coordinator = MultiTabCoordinator(self.browser)
        return self._tab_coordinator

    def _get_vision_pipeline(self):
        """Lazy-initialize and return the VisionPipeline.

        Returns:
            VisionPipeline: The visual perception pipeline.
        """
        if self._vision_pipeline is None:
            from tools.browser.vision.pipeline import VisionPipeline
            self._vision_pipeline = VisionPipeline(self.browser)
        return self._vision_pipeline

    def execute_to_json(self, action_dict: Dict[str, Any]) -> str:
        """Execute action and serialize the standardized result directly to JSON.

        Args:
            action_dict (Dict[str, Any]): Dictionary of action parameters.

        Returns:
            str: JSON representation of the ActionResult.
        """
        res = self.execute(action_dict)
        from tools.browser.serializer import to_json_str
        return to_json_str(res.to_dict(), indent=2)
