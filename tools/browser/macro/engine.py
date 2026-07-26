"""Macro Action Engine — Execution orchestration middleware.

Coordinates parsing, parameters validation, execution trace, retries,
timeouts, and rollback routines on failure.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from tools.browser.macro.base import (
    MacroError,
    MacroExecutionContext,
    MacroExecutionError,
    MacroRollbackError,
    MacroValidationError,
    global_registry,
)
from tools.browser.models.response import ActionResult, ActionMetrics

logger = logging.getLogger("MacroEngine.Orchestrator")


class MacroActionEngine:
    """Orchestrates macro execution lifecycle and rollback strategies.

    This engine is the central entry point for high-level macro/skill operations
    dispatched by the BrowserActionExecutor.

    Key responsibilities:
        1. Parse and validate macro parameters.
        2. Setup macro execution context (variables, trace logs, browser state checkpoints).
        3. Dispatch execution to the registered BaseMacro subclass.
        4. Manage retry policies and execution timeouts.
        5. Catch failures and initiate rollback recovery.
    """

    def __init__(self, executor: Any) -> None:
        """Initialize the macro engine.

        Args:
            executor: The active BrowserActionExecutor.
        """
        self.executor = executor
        self.browser = executor.browser
        self.registry = global_registry
        self._logger = logger

    def run_macro(self, macro_name: str, action_dict: Dict[str, Any]) -> ActionResult:
        """Execute a macro by name with provided arguments.

        Loads the macro class, runs parameters validation, sets up execution trace,
        and runs execution. If a sub-action step fails, performs rollback recovery
        to revert browser state changes before raising/returning the error.

        Args:
            macro_name: The name of the macro (e.g. 'macro_search').
            action_dict: The action parameter dictionary.

        Returns:
            ActionResult: The output representation of the macro.
        """
        start_time = time.time()
        macro_cls = self.registry.get(macro_name)

        if not macro_cls:
            self._logger.error(f"Macro '{macro_name}' is not registered.")
            return ActionResult(
                url=self.browser.get_current_url().data or "about:blank",
                title="",
                success=False,
                errors=[f"Unknown macro action: '{macro_name}'"],
            )

        self._logger.info(f"Preparing execution of macro '{macro_name}'...")

        # Setup Execution Context
        context = MacroExecutionContext(self.executor, action_dict)
        macro_instance = macro_cls(context)

        # Parse & Validate
        try:
            macro_instance.validate(action_dict)
        except MacroValidationError as mve:
            self._logger.warning(f"Parameter validation failed for macro '{macro_name}': {mve}")
            return ActionResult(
                url=self.browser.get_current_url().data or "about:blank",
                title="",
                success=False,
                errors=[f"Macro validation failed: {mve}"],
            )

        # Retry configuration settings
        retries_limit = int(action_dict.get("retry_limit") or action_dict.get("retries") or 0)
        retry_delay = float(action_dict.get("retry_delay") or 1.0)

        attempt = 0
        while True:
            try:
                # Execute Macro
                res = macro_instance.execute(action_dict)
                duration_ms = (time.time() - start_time) * 1000.0

                # Inject metrics
                if res.metrics is None:
                    res.metrics = ActionMetrics(
                        execution_time_ms=duration_ms,
                        retries_attempted=attempt,
                    )
                else:
                    res.metrics.execution_time_ms = duration_ms
                    res.metrics.retries_attempted = attempt

                # Add trace to result verification details
                if res.verification is None:
                    res.verification = {}
                res.verification["macro_trace"] = context.trace

                self._logger.info(
                    f"Macro '{macro_name}' completed successfully on attempt {attempt + 1} "
                    f"({duration_ms:.1f}ms)."
                )
                return res

            except (MacroExecutionError, Exception) as e:
                attempt += 1
                self._logger.error(
                    f"Macro execution failed (attempt {attempt}/{retries_limit + 1}): {e}"
                )

                # Attempt Rollback
                try:
                    macro_instance.rollback(action_dict)
                except MacroRollbackError as mre:
                    self._logger.error(f"Rollback failed: {mre}")
                except Exception as ex:
                    self._logger.error(f"Unexpected exception during rollback: {ex}")

                # Retry check
                if attempt <= retries_limit:
                    self._logger.info(f"Retrying macro '{macro_name}' in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue

                duration_ms = (time.time() - start_time) * 1000.0
                errors = [f"Macro execution failed: {e}"]
                if isinstance(e, MacroExecutionError) and getattr(e, "__cause__", None):
                    errors.append(f"Caused by: {e.__cause__}")

                return ActionResult(
                    url=self.browser.get_current_url().data or "about:blank",
                    title="",
                    success=False,
                    errors=errors,
                    verification={"macro_trace": context.trace},
                    metrics=ActionMetrics(
                        execution_time_ms=duration_ms,
                        retries_attempted=attempt - 1,
                    ),
                )
