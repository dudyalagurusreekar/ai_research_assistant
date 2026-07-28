"""Browser self-healing strategies.

Implements concrete recovery strategies for DOM stale elements, overlays,
timeouts, session state loss, browser crashes, and network disconnections.
"""

import logging
import time
import urllib.request
from typing import Any, Dict, Optional

from tools.browser.models.response import ActionResult
from tools.browser.recovery.base import (
    BaseRecoveryStrategy,
    RecoveryContext,
    RecoveryResult,
    SessionRestorationError,
)

logger = logging.getLogger("RecoveryEngine.Strategies")


def _js_string(s: str) -> str:
    """Safely escape a Python string for use in a JavaScript string literal."""
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _re_execute_action(ctx: RecoveryContext, action_dict: Optional[Dict[str, Any]] = None) -> ActionResult:
    """Safely re-executes the action by bypassing the recovery handler loop.

    Avoids recursion by initializing a clean, isolated BrowserActionExecutor.
    """
    from tools.browser.executor import BrowserActionExecutor
    from tools.browser.state_manager import BrowserStateMemoryManager

    # Instantiate executor bypassing recovery hooks recursion
    temp_executor = BrowserActionExecutor.__new__(BrowserActionExecutor)
    temp_executor.browser = ctx.browser
    temp_executor._logger = logger
    temp_executor.history = []
    temp_executor.state_manager = BrowserStateMemoryManager(ctx.browser, max_history_size=1)
    temp_executor._recovery_engine = None  # Block recursion

    target_action = action_dict or ctx.action_dict
    return temp_executor.execute(target_action)


class RetryWithBackoff(BaseRecoveryStrategy):
    """Retries the original action with exponential backoff delay."""

    def __init__(self, base_delay_s: float = 0.5, max_delay_s: float = 4.0) -> None:
        self.base_delay_s = base_delay_s
        self.max_delay_s = max_delay_s

    @property
    def name(self) -> str:
        return "retry_with_backoff"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        # Calculate exponential backoff
        delay = min(self.base_delay_s * (2 ** (ctx.attempt_number - 1)), self.max_delay_s)
        logger.info(f"RetryWithBackoff sleeping for {delay:.1f}s (attempt {ctx.attempt_number})")
        time.sleep(delay)

        res = _re_execute_action(ctx)
        return RecoveryResult(
            success=res.success,
            strategy_used=self.name,
            attempts=1,
            message=f"Retried original action after {delay:.1f}s backoff delay.",
            action_result=res,
        )


class WaitForDOMStability(BaseRecoveryStrategy):
    """Waits for network idle and DOM mutations to settle before retrying."""

    @property
    def name(self) -> str:
        return "wait_for_dom_stability"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        logger.info("WaitForDOMStability waiting for network and DOM mutations to settle...")
        
        # 1. Wait for network idle
        try:
            ctx.browser.wait_for_network_idle(timeout=3.0)
        except Exception:
            pass

        # 2. Wait for a short DOM settle interval via MutationObserver
        settle_js = """
        new Promise(r => {
            const observer = new MutationObserver(() => {});
            observer.observe(document.body, { childList: true, subtree: true });
            setTimeout(() => {
                observer.disconnect();
                r();
            }, 500);
        })
        """
        try:
            ctx.browser.execute_javascript(settle_js)
        except Exception:
            time.sleep(0.5)  # Fallback sleep

        res = _re_execute_action(ctx)
        return RecoveryResult(
            success=res.success,
            strategy_used=self.name,
            attempts=1,
            message="Waited for DOM mutations to settle before retrying.",
            action_result=res,
        )


class AlternativeSelectorDiscovery(BaseRecoveryStrategy):
    """Discovers alternative CSS selectors for a missing/stale element."""

    @property
    def name(self) -> str:
        return "alternative_selector_discovery"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        original_selector = ctx.action_dict.get("selector", "")
        if not original_selector:
            return RecoveryResult(
                success=False,
                strategy_used=self.name,
                message="Cannot attempt selector discovery: no selector provided in parameters.",
            )

        logger.info(f"AlternativeSelectorDiscovery checking elements for '{original_selector}'...")

        discovery_script = f"""
        (() => {{
            const sel = {_js_string(original_selector)};
            
            // Strategy 1: Check by ID suffix/fragment
            const idMatch = sel.match(/#([\\w-]+)/);
            if (idMatch) {{
                const el = document.getElementById(idMatch[1]);
                if (el) return '#' + idMatch[1];
            }}

            // Strategy 2: Check by text content match for links and buttons
            const textMatch = sel.match(/text[=~]*["']?([^"'\\]]+)/i);
            if (textMatch) {{
                const text = textMatch[1].trim();
                for (const tag of ['a', 'button', 'input[type=submit]', 'label']) {{
                    for (const el of document.querySelectorAll(tag)) {{
                        if (el.textContent && el.textContent.trim().includes(text)) {{
                            if (el.id) return '#' + el.id;
                            if (el.name) return tag + '[name="' + el.name + '"]';
                            if (el.className) return tag + '.' + el.className.trim().split(/\\s+/)[0];
                        }}
                    }}
                }}
            }}

            // Strategy 3: Attribute checks (aria-label, placeholder, name, testid)
            for (const attr of ['name', 'aria-label', 'placeholder', 'data-testid']) {{
                const attrMatch = sel.match(new RegExp('\\\\[' + attr + '=["\\'](.*?)["\\']\\\\]'));
                if (attrMatch) {{
                    const el = document.querySelector('[' + attr + '="' + attrMatch[1] + '"]');
                    if (el) return '[' + attr + '="' + attrMatch[1] + '"]';
                }}
            }}
            return null;
        }})()
        """

        alt_res = ctx.browser.execute_javascript(discovery_script)
        alt_selector = alt_res.data if alt_res.success else None

        if not alt_selector or alt_selector == original_selector:
            return RecoveryResult(
                success=False,
                strategy_used=self.name,
                message=f"No alternative selector discovered for original selector: '{original_selector}'",
            )

        logger.info(f"AlternativeSelectorDiscovery found: '{alt_selector}'")

        # Retry using the new selector
        new_action = dict(ctx.action_dict)
        new_action["selector"] = alt_selector

        res = _re_execute_action(ctx, new_action)
        return RecoveryResult(
            success=res.success,
            strategy_used=self.name,
            attempts=1,
            message=f"Recovered by discovering alternative selector: '{alt_selector}'",
            action_result=res,
            discovered_alternative_selector=alt_selector,
        )


class DismissOverlay(BaseRecoveryStrategy):
    """Dismisses cookie banners, popups, and obscure fixed overlays blocking actions."""

    @property
    def name(self) -> str:
        return "dismiss_overlay"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        logger.info("DismissOverlay scanning page for blocking overlays/modals...")

        dismiss_js = """
        (() => {
            const overlaySelectors = [
                '[id*="cookie"] button', '[class*="cookie"] button',
                '[id*="consent"] button', '[class*="consent"] button',
                '[id*="gdpr"] button', '[class*="gdpr"] button',
                'button[aria-label*="close"]', 'button[aria-label*="Close"]',
                'button[aria-label*="dismiss"]', 'button[aria-label*="Dismiss"]',
                '.modal-close', '.close-button', '[data-dismiss="modal"]',
            ];
            let clicked = 0;
            for (const sel of overlaySelectors) {
                try {
                    const elements = document.querySelectorAll(sel);
                    for (const el of elements) {
                        if (el.offsetParent !== null) {
                            el.click();
                            clicked++;
                        }
                    }
                } catch(e) {}
            }
            
            // Remove blocking full-page overlays with high z-index
            let removed = 0;
            for (const el of document.querySelectorAll('div, aside, section')) {
                try {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' && style.zIndex > 999 
                        && el.offsetWidth > window.innerWidth * 0.5) {
                        el.remove();
                        removed++;
                    }
                } catch(e) {}
            }
            return `Clicked ${clicked} buttons, removed ${removed} blocking overlays.`;
        })()
        """
        res_js = ctx.browser.execute_javascript(dismiss_js)
        msg = res_js.data if res_js.success else "Overlay script error"
        logger.info(f"DismissOverlay: {msg}")

        time.sleep(0.3)  # Wait for transition/animations to complete

        res = _re_execute_action(ctx)
        return RecoveryResult(
            success=res.success,
            strategy_used=self.name,
            attempts=1,
            message=f"Attempted overlay dismissal: {msg}",
            action_result=res,
        )


class PageReload(BaseRecoveryStrategy):
    """Reloads the page and retries the action."""

    @property
    def name(self) -> str:
        return "page_reload"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        url_res = ctx.browser.get_current_url()
        current_url = url_res.data if url_res.success else None

        if not current_url or current_url == "about:blank":
            return RecoveryResult(
                success=False,
                strategy_used=self.name,
                message="Cannot reload: browser is currently not showing a valid URL.",
            )

        logger.info(f"PageReload reloading URL: {current_url}")
        ctx.browser.open_url(current_url)
        time.sleep(0.5)

        res = _re_execute_action(ctx)
        return RecoveryResult(
            success=res.success,
            strategy_used=self.name,
            attempts=1,
            message=f"Reloaded URL '{current_url}' before retrying action.",
            action_result=res,
        )


class ScrollIntoView(BaseRecoveryStrategy):
    """Scrolls target element into center viewport before retrying."""

    @property
    def name(self) -> str:
        return "scroll_into_view"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        selector = ctx.action_dict.get("selector", "")
        if not selector:
            return RecoveryResult(
                success=False,
                strategy_used=self.name,
                message="Cannot scroll: no selector provided in parameters.",
            )

        logger.info(f"ScrollIntoView scrolling target element '{selector}' into view...")
        scroll_js = f"document.querySelector({_js_string(selector)})?.scrollIntoView({{behavior:'instant',block:'center'}})"
        ctx.browser.execute_javascript(scroll_js)
        time.sleep(0.3)

        res = _re_execute_action(ctx)
        return RecoveryResult(
            success=res.success,
            strategy_used=self.name,
            attempts=1,
            message=f"Scrolled element '{selector}' into view before retrying.",
            action_result=res,
        )


class SessionRefresh(BaseRecoveryStrategy):
    """Re-navigates to URL to restore session parameters."""

    @property
    def name(self) -> str:
        return "session_refresh"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        url_res = ctx.browser.get_current_url()
        current_url = url_res.data if url_res.success else None

        if current_url and current_url != "about:blank":
            logger.info(f"SessionRefresh navigating back to URL to reset context: {current_url}")
            ctx.browser.open_url(current_url)
            try:
                ctx.browser.wait_for_network_idle(timeout=5.0)
            except Exception:
                pass

        res = _re_execute_action(ctx)
        return RecoveryResult(
            success=res.success,
            strategy_used=self.name,
            attempts=1,
            message=f"Refreshed session at '{current_url}' before retrying.",
            action_result=res,
        )


class BrowserCrashRecovery(BaseRecoveryStrategy):
    """Recovers from a browser crash by spawning a new context and navigating back."""

    @property
    def name(self) -> str:
        return "browser_crash_recovery"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        logger.warning("BrowserCrashRecovery initiating browser session restoration...")

        # 1. Capture last known URL
        url_res = ctx.browser.get_current_url()
        last_url = url_res.data if url_res.success else ctx.action_dict.get("url")

        if not last_url or last_url == "about:blank":
            # Fallback to history
            if ctx.browser.history:
                last_url = ctx.browser.history[-1]

        # 2. Tear down the browser / automation engine
        try:
            if hasattr(ctx.browser, "automation"):
                ctx.browser.automation.close()
        except Exception as e:
            logger.warning(f"Error during crashed browser close (non-fatal): {e}")

        # 3. Create/initialize a new Automation Engine context
        try:
            from tools.browser.automation.engine import BrowserAutomationEngine
            ctx.browser._automation_engine = BrowserAutomationEngine(config=ctx.browser.config)
            ctx.browser.automation._run_sync(ctx.browser.automation.strategy.initialize())
        except Exception as e:
            raise SessionRestorationError(f"Failed to spawn new browser context: {e}") from e

        # 4. Navigate back to the last known URL
        if last_url and last_url != "about:blank":
            logger.info(f"BrowserCrashRecovery restored! Navigating back to: {last_url}")
            try:
                ctx.browser.open_url(last_url)
                ctx.browser.wait_for_network_idle(timeout=5.0)
            except Exception as e:
                logger.warning(f"Failed to load page during recovery navigation: {e}")

        # 5. Re-execute the action
        res = _re_execute_action(ctx)
        return RecoveryResult(
            success=res.success,
            strategy_used=self.name,
            attempts=1,
            message=f"Successfully recovered from browser crash. Spawned context and loaded page '{last_url}'.",
            action_result=res,
        )


class NetworkInterruptionRecovery(BaseRecoveryStrategy):
    """Waits for network connectivity to be restored before retrying the action."""

    def __init__(self, check_url: str = "https://www.google.com", max_wait_s: float = 15.0) -> None:
        self.check_url = check_url
        self.max_wait_s = max_wait_s

    @property
    def name(self) -> str:
        return "network_interruption_recovery"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        logger.warning(f"NetworkInterruptionRecovery checking network connectivity (limit {self.max_wait_s}s)...")

        start = time.time()
        attempt = 0
        online = False

        while time.time() - start < self.max_wait_s:
            attempt += 1
            try:
                # Lightweight fetch ping
                urllib.request.urlopen(self.check_url, timeout=2.0)
                online = True
                logger.info(f"Network connection restored on ping attempt {attempt}!")
                break
            except Exception:
                # Exponential backoff wait
                sleep_time = min(0.5 * (2 ** (attempt - 1)), 3.0)
                logger.debug(f"Network offline. Sleeping for {sleep_time:.1f}s...")
                time.sleep(sleep_time)

        if not online:
            return RecoveryResult(
                success=False,
                strategy_used=self.name,
                message=f"Network remained offline after waiting {self.max_wait_s} seconds.",
            )

        # Reload the page to sync state
        try:
            url_res = ctx.browser.get_current_url()
            curr_url = url_res.data if url_res.success else None
            if curr_url and curr_url != "about:blank":
                ctx.browser.open_url(curr_url)
        except Exception:
            pass

        # Retry the action
        res = _re_execute_action(ctx)
        return RecoveryResult(
            success=res.success,
            strategy_used=self.name,
            attempts=attempt,
            message="Network connectivity restored. Re-executed original action.",
            action_result=res,
        )


class CaptchaRecoveryStrategy(BaseRecoveryStrategy):
    """Detects and attempts to handle or report CAPTCHA blockages."""

    @property
    def name(self) -> str:
        return "captcha_recovery"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        logger.info("CaptchaRecoveryStrategy attempting to handle CAPTCHA...")
        
        # In a real enterprise system, we might integrate 2captcha or anti-captcha APIs here.
        # For now, we will attempt to find a 'solve' button or wait.
        
        solve_js = """
        (() => {
            const btn = document.querySelector('.cf-turnstile-wrapper, iframe[title="reCAPTCHA"], #challenge-stage');
            if (btn) {
                return 'CAPTCHA element found.';
            }
            return null;
        })()
        """
        res_js = ctx.browser.execute_javascript(solve_js)
        if res_js.success and res_js.data:
            logger.info("CAPTCHA widget detected on page.")
            
        # As an automated agent without a solving service, we pause and then return a failure
        # that explicitly tells the planner to abort this URL.
        time.sleep(2.0)
        
        failed_res = ActionResult(
            url=ctx.failed_result.url,
            title=ctx.failed_result.title,
            success=False,
            errors=ctx.failed_result.errors + ["CAPTCHA blocked access. Requires human intervention or proxy rotation."],
            data={"planner_feedback": "A CAPTCHA or Bot-Protection wall is blocking this page. Stop trying this domain and use a different search strategy or URL."},
        )
        
        return RecoveryResult(
            success=False,
            strategy_used=self.name,
            attempts=1,
            message="CAPTCHA detected. Automated recovery not possible without solver.",
            action_result=failed_res,
        )


class PlannerFeedbackStrategy(BaseRecoveryStrategy):
    """Structured feedback helper strategy for planning/graph routing.

    Exposures error details as natural language explanations for the
    planner graph to replan if retry attempts fail.
    """

    @property
    def name(self) -> str:
        return "planner_feedback_strategy"

    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        logger.warning("PlannerFeedbackStrategy packing action failure context for planner feedback loop...")

        action_name = ctx.action_dict.get("action", "unknown")
        selector = ctx.action_dict.get("selector", "")
        category = ctx.error_category.value if hasattr(ctx.error_category, "value") else str(ctx.error_category)

        feedback_message = (
            f"Action '{action_name}' failed completely with category '{category}'. "
            f"Error details: '{ctx.error_message}'. "
        )

        if selector:
            feedback_message += (
                f"The target selector '{selector}' was either not found, obscured, or became stale. "
                f"Consider selecting an alternative element, navigating elsewhere, or checking page layout."
            )
        else:
            feedback_message += (
                "Verify input parameters, check internet connectivity, or wait for the site session to refresh."
            )

        failed_res = ActionResult(
            url=ctx.failed_result.url,
            title=ctx.failed_result.title,
            success=False,
            errors=ctx.failed_result.errors + [feedback_message],
            data={"planner_feedback": feedback_message},
        )

        return RecoveryResult(
            success=False,  # This strategy intentionally reports failure to trigger replanning
            strategy_used=self.name,
            attempts=1,
            message="Structured failure feedback sent to the planner.",
            action_result=failed_res,
        )
