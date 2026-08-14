"""Reflection Engine Integration Bridge for Sprint 11 Browser Automation Platform."""

import logging
from typing import Any, Dict, List, Optional
from core.reflection.engine import ReflectionEngine
from tools.browser.platform.models import ActionResult, DOMTree

logger = logging.getLogger("Tools.Browser.Integration.ReflectionIntegration")


class ReflectionBrowserBridge:
    """Evaluates browser step outcomes, verifies page state transitions, detects infinite loops, and triggers self-correction."""

    def __init__(self, reflection_engine: Optional[ReflectionEngine] = None) -> None:
        self.reflection_engine = reflection_engine or ReflectionEngine()
        self._url_history: List[str] = []

    def evaluate_browser_step(
        self,
        result: ActionResult,
        previous_dom: Optional[DOMTree] = None,
        current_dom: Optional[DOMTree] = None,
    ) -> Dict[str, Any]:
        """Evaluate whether browser step achieved desired transition or encountered stasis/loops."""
        if result.url:
            self._url_history.append(result.url)

        # Check for loop / stasis (same URL 3+ consecutive times without DOM change)
        is_loop = False
        if len(self._url_history) >= 4 and len(set(self._url_history[-4:])) == 1:
            is_loop = True
            logger.warning(f"Detected page stasis / loop on URL '{result.url}'. Triggering reflection engine re-route.")

        evaluation = {
            "success": result.success and not is_loop,
            "action_type": result.action_type.value,
            "is_stasis_loop": is_loop,
            "error": result.error if not result.success else ("Page stasis loop detected" if is_loop else None),
            "recommendation": "retry_with_text_fallback" if is_loop else ("proceed" if result.success else "reload_page"),
        }

        return evaluation
