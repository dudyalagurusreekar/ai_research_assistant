"""Macro Action Engine Proxy.

Maintains backward-compatibility for existing imports of MacroActionEngine
by routing execution to the new registry-based macro package under tools/browser/macro/.
"""

import logging
from typing import Any, Dict

from tools.browser.models.response import ActionResult
from tools.browser.macro.engine import MacroActionEngine as NewMacroActionEngine

logger = logging.getLogger("MacroActionEngineProxy")


class MacroActionEngine:
    """Proxy class routing macro execution requests to the new registry-based package."""

    def __init__(self, executor: Any) -> None:
        """Initialize the macro engine proxy.

        Args:
            executor: The active BrowserActionExecutor.
        """
        self._new_engine = NewMacroActionEngine(executor)
        self.executor = executor
        self.browser = executor.browser
        self._logger = logger

    def run_macro(self, macro_name: str, action_dict: Dict[str, Any]) -> ActionResult:
        """Forward macro execution to the registry-based package engine.

        Args:
            macro_name: Mapped name (e.g. 'macro_search').
            action_dict: Action arguments.

        Returns:
            ActionResult: The output ActionResult.
        """
        self._logger.info(f"Proxy routing macro execution: '{macro_name}'")
        return self._new_engine.run_macro(macro_name, action_dict)
