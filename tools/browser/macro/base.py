"""Base classes and execution context for the Macro Action Engine.

Defines the core lifecycle, registry mechanism, and execution context for
high-level browser skills (macros).
"""

import abc
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Type

from tools.browser.core.browser import Browser
from tools.browser.models.response import ActionResult

logger = logging.getLogger("MacroEngine.Base")


class MacroError(Exception):
    """Base class for all macro-related errors."""
    pass


class MacroValidationError(MacroError):
    """Raised when macro parameter validation fails."""
    pass


class MacroExecutionError(MacroError):
    """Raised when a macro execution step fails."""
    pass


class MacroRollbackError(MacroError):
    """Raised when a rollback operation fails during recovery."""
    pass


class MacroExecutionContext:
    """Shared state container for a single macro execution run.

    Provides tracing, variable collection, checkpointing, and access to
    subsystems for the executing macro.

    Attributes:
        executor: Reference to the BrowserActionExecutor.
        browser: Reference to the Browser facade.
        session_id: Unique identifier for the macro execution.
        variables: Collected observation dictionary.
        trace: Step-by-step history of executed actions.
        checkpoints: List of saved browser state snapshot IDs.
    """

    def __init__(self, executor: Any, action_dict: Dict[str, Any]) -> None:
        """Initialize the execution context.

        Args:
            executor: The active BrowserActionExecutor.
            action_dict: The action dictionary that invoked the macro.
        """
        self.executor = executor
        self.browser: Browser = executor.browser
        self.session_id: str = f"macro_run_{uuid.uuid4().hex[:8]}"
        self.variables: Dict[str, Any] = {}
        self.trace: List[Dict[str, Any]] = []
        self.checkpoints: List[str] = []
        self.start_time: float = time.time()
        self._logger = logger

    def record_step(self, action: str, success: bool, duration_ms: float, error: Optional[str] = None) -> None:
        """Record a sub-action step in the execution trace.

        Args:
            action: Action verb/name.
            success: Whether the sub-action was successful.
            duration_ms: Execution duration in milliseconds.
            error: Optional error message on failure.
        """
        step = {
            "timestamp": time.time(),
            "action": action,
            "success": success,
            "duration_ms": duration_ms,
            "error": error,
        }
        self.trace.append(step)
        self._logger.debug(
            f"[{self.session_id}] Step logged: {action} (success={success}, duration={duration_ms:.1f}ms)"
        )

    def create_checkpoint(self) -> str:
        """Create a browser state checkpoint.

        Uses the executor's state manager to capture the current state.

        Returns:
            str: The checkpoint/snapshot identifier.
        """
        try:
            # Check if executor has state_manager
            state_manager = getattr(self.executor, "state_manager", None)
            if state_manager:
                snapshot = state_manager.capture_state({"action": f"checkpoint_{self.session_id}"})
                checkpoint_id = f"cp_{uuid.uuid4().hex[:6]}"
                # Store snapshot in context variables for retrieval
                self.variables[checkpoint_id] = snapshot
                self.checkpoints.append(checkpoint_id)
                self._logger.info(f"[{self.session_id}] Created state checkpoint: {checkpoint_id}")
                return checkpoint_id
        except Exception as e:
            self._logger.warning(f"Failed to create checkpoint: {e}")
        return ""

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore a previously saved browser state checkpoint.

        Args:
            checkpoint_id: The checkpoint identifier.

        Returns:
            bool: True if successfully restored, False otherwise.
        """
        if not checkpoint_id or checkpoint_id not in self.checkpoints:
            self._logger.warning(f"Checkpoint '{checkpoint_id}' not found.")
            return False

        try:
            snapshot = self.variables.get(checkpoint_id)
            if snapshot and getattr(self.executor, "state_manager", None):
                # Restore via state manager
                self.executor.state_manager.restore_state(snapshot)
                self._logger.info(f"[{self.session_id}] Restored state checkpoint: {checkpoint_id}")
                return True
        except Exception as e:
            self._logger.error(f"Failed to restore checkpoint '{checkpoint_id}': {e}")
        return False


class BaseMacro(abc.ABC):
    """Abstract base class for all browser macros (high-level browser skills).

    Provides the structure for parameter validation, execution, and rollback recovery.
    """

    def __init__(self, context: MacroExecutionContext) -> None:
        """Initialize the macro with its execution context.

        Args:
            context: The macro execution context.
        """
        self.context = context
        self._logger = logging.getLogger(f"MacroEngine.{self.__class__.__name__}")

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The macro string identifier (e.g., 'macro_search')."""
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """A brief description of what the macro accomplishes."""
        pass

    @abc.abstractmethod
    def validate(self, params: Dict[str, Any]) -> None:
        """Validate input parameters.

        Args:
            params: Parameters dictionary.

        Raises:
            MacroValidationError: If validation fails.
        """
        pass

    @abc.abstractmethod
    def execute(self, params: Dict[str, Any]) -> ActionResult:
        """Run the macro logic.

        Args:
            params: Parameters dictionary.

        Returns:
            ActionResult: The outcome of the macro execution.

        Raises:
            MacroExecutionError: If execution fails.
        """
        pass

    def rollback(self, params: Dict[str, Any]) -> None:
        """Optionally roll back browser changes on failure.

        Args:
            params: Parameters dictionary.

        Raises:
            MacroRollbackError: If rollback logic fails.
        """
        # Default implementation restores the most recent checkpoint if one exists
        if self.context.checkpoints:
            last_checkpoint = self.context.checkpoints[-1]
            success = self.context.restore_checkpoint(last_checkpoint)
            if not success:
                raise MacroRollbackError(f"Failed to restore checkpoint '{last_checkpoint}'.")
        else:
            self._logger.debug("No checkpoints to restore during rollback.")

    def run_sub_action(self, action_dict: Dict[str, Any]) -> ActionResult:
        """Run a single sub-action step through the action executor.

        Updates the execution context trace automatically.

        Args:
            action_dict: The action dictionary.

        Returns:
            ActionResult: The sub-action result.

        Raises:
            MacroExecutionError: If sub-action fails.
        """
        action_name = action_dict.get("action", "unknown")
        start = time.time()
        try:
            res = self.context.executor.execute(action_dict)
            duration = (time.time() - start) * 1000.0
            error_msg = "; ".join(res.errors) if res.errors else None
            self.context.record_step(action_name, res.success, duration, error_msg)
            
            if not res.success:
                raise MacroExecutionError(
                    f"Sub-action '{action_name}' failed: {error_msg or 'No error message details provided.'}"
                )
            return res
        except Exception as e:
            duration = (time.time() - start) * 1000.0
            if not isinstance(e, MacroExecutionError):
                self.context.record_step(action_name, False, duration, str(e))
                raise MacroExecutionError(f"Sub-action '{action_name}' encountered exception: {e}") from e
            raise


class MacroRegistry:
    """Thread-safe registry mapping macro names to their class definitions."""

    def __init__(self) -> None:
        self._macros: Dict[str, Type[BaseMacro]] = {}

    def register(self, name: str, cls: Type[BaseMacro]) -> None:
        """Register a macro class in the global registry.

        Args:
            name: The macro identifier (e.g. 'macro_search').
            cls: The macro class.
        """
        self._macros[name.lower()] = cls
        logger.debug(f"Registered macro '{name.lower()}' ({cls.__name__})")

    def get(self, name: str) -> Optional[Type[BaseMacro]]:
        """Retrieve a macro class by name.

        Args:
            name: The macro name.

        Returns:
            Optional[Type[BaseMacro]]: The class definition, or None.
        """
        return self._macros.get(name.lower())

    def list_macros(self) -> Dict[str, str]:
        """List all registered macros.

        Returns:
            Dict[str, str]: Mapping of macro name to its description.
        """
        res = {}
        for name, cls in self._macros.items():
            try:
                # Instantiate with None context to evaluate property values safely
                instance = cls(context=None)
                res[name] = instance.description
            except Exception:
                res[name] = str(getattr(cls, "description", ""))
        return res


# Global Registry Instance
global_registry = MacroRegistry()


def register_macro(name: str):
    """Decorator to register a macro class in the global registry.

    Args:
        name: The macro string identifier.
    """
    def decorator(cls: Type[BaseMacro]):
        global_registry.register(name, cls)
        return cls
    return decorator
