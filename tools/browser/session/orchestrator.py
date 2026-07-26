"""Session Orchestrator — Top-level coordinator for browser agent sessions.

Owns the full session lifecycle: initialization, multi-goal execution,
pause/resume, persistence, cleanup, and event dispatch. Coordinates all
lower-level components (Browser, Executor, Planner, Memory, State, Recovery,
Context, Reporting) into a unified session abstraction.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.context_manager import ContextLifecycleManager
from tools.browser.core.browser import Browser
from tools.browser.executor import BrowserActionExecutor
from tools.browser.memory.manager import MemoryManager
from tools.browser.recovery import RecoveryEngine
from tools.browser.reporting import ReportingEngine
from tools.browser.session.hooks import LoggingHook, SessionHook
from tools.browser.session.models import (
    GoalResult,
    SessionConfig,
    SessionMetadata,
    SessionState,
)
from tools.browser.session.persistence import SessionPersistence
from tools.browser.state_manager import BrowserStateMemoryManager

logger = logging.getLogger("SessionOrchestrator")


class SessionError(Exception):
    """Raised when a session operation violates lifecycle constraints."""
    pass


class SessionOrchestrator:
    """Production-grade session lifecycle coordinator for the autonomous browser agent.

    The SessionOrchestrator is the single top-level entry point for running browser
    automation tasks. It manages the full lifecycle from browser initialization through
    multi-goal execution to graceful cleanup.

    Architecture position:
        - Sits above the BrowserPlanner, BrowserActionExecutor, and all other components
        - Owns and wires together all subsystem instances
        - Provides session-level concerns: persistence, event hooks, timeout management
        - Delegates actual goal execution to BrowserPlanner

    Key responsibilities:
        1. Browser lifecycle (launch, cleanup, resource release)
        2. Multi-goal sequential execution within a session
        3. Session state machine (INITIALIZING → ACTIVE → PAUSED/COMPLETING → CLOSED)
        4. Per-goal timeout enforcement
        5. Memory consolidation between goals
        6. Session persistence and crash recovery
        7. Event hook dispatch for logging, metrics, and custom observers

    Example usage::

        config = SessionConfig(max_goals=10, goal_timeout_seconds=120)
        orchestrator = SessionOrchestrator(config=config)
        orchestrator.start()

        result = orchestrator.run_goal("Search for Python tutorials on Google")
        print(result.final_output)

        orchestrator.close()

    Attributes:
        config: Session configuration parameters.
        metadata: Aggregate session tracking metadata.
        browser: The Browser instance owned by this session.
        executor: The BrowserActionExecutor middleware.
        memory_manager: Multi-layer memory system.
        state_manager: Browser state snapshot manager.
        recovery_engine: Error classification and self-healing engine.
        context_manager: Context bloat management and artifact offloading.
        persistence: Session checkpoint save/load handler.
        hooks: List of registered session event hooks.
    """

    # Valid state transitions for the session state machine
    _VALID_TRANSITIONS: Dict[SessionState, List[SessionState]] = {
        SessionState.INITIALIZING: [SessionState.ACTIVE, SessionState.ERROR, SessionState.CLOSED],
        SessionState.ACTIVE: [SessionState.PAUSED, SessionState.COMPLETING, SessionState.ERROR],
        SessionState.PAUSED: [SessionState.ACTIVE, SessionState.CLOSED, SessionState.ERROR],
        SessionState.COMPLETING: [SessionState.CLOSED, SessionState.ERROR],
        SessionState.CLOSED: [],  # Terminal state
        SessionState.ERROR: [SessionState.CLOSED],  # Can only close from error
    }

    def __init__(
        self,
        config: Optional[SessionConfig] = None,
        browser_config: Optional[BrowserConfig] = None,
        browser: Optional[Browser] = None,
        memory_manager: Optional[MemoryManager] = None,
        hooks: Optional[List[SessionHook]] = None,
    ) -> None:
        """Initialize the Session Orchestrator.

        All subsystem components are lazily initialized during ``start()``
        to allow configuration to be finalized before resource allocation.

        Args:
            config: Session configuration. Defaults to SessionConfig() if not provided.
            browser_config: Browser-level configuration for the Playwright engine.
            browser: Optional pre-existing Browser instance (for testing/reuse).
            memory_manager: Optional pre-existing MemoryManager instance.
            hooks: Optional list of SessionHook observers. A LoggingHook is always
                added by default if no hooks are provided.
        """
        self.config = config or SessionConfig()
        self._browser_config = browser_config or BrowserConfig(
            engine_type=BrowserEngineType.PLAYWRIGHT
        )

        # Subsystem instances (initialized during start())
        self.browser: Optional[Browser] = browser
        self.executor: Optional[BrowserActionExecutor] = None
        self.memory_manager: Optional[MemoryManager] = memory_manager
        self.state_manager: Optional[BrowserStateMemoryManager] = None
        self.recovery_engine: Optional[RecoveryEngine] = None
        self.context_manager: Optional[ContextLifecycleManager] = None

        # Session tracking
        self.metadata = SessionMetadata()
        self._session_start_time: float = 0.0

        # Persistence
        self.persistence = SessionPersistence(self.config.persist_directory)

        # Event hooks
        self.hooks: List[SessionHook] = hooks or [LoggingHook()]

        self._logger = logger

    def _transition_state(self, new_state: SessionState) -> None:
        """Execute a session state transition with validation and hook dispatch.

        Args:
            new_state: The target session state.

        Raises:
            SessionError: If the transition is not valid from the current state.
        """
        old_state = self.metadata.state
        valid_targets = self._VALID_TRANSITIONS.get(old_state, [])

        if new_state not in valid_targets:
            raise SessionError(
                f"Invalid state transition: {old_state.value} → {new_state.value}. "
                f"Allowed transitions from {old_state.value}: "
                f"{[s.value for s in valid_targets]}"
            )

        self.metadata.state = new_state
        self._logger.debug(f"State transition: {old_state.value} → {new_state.value}")

        for hook in self.hooks:
            try:
                hook.on_state_change(old_state, new_state, self.metadata)
            except Exception as e:
                self._logger.warning(f"Hook error in on_state_change: {e}")

    def _dispatch_hook(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """Safely dispatch an event to all registered hooks.

        Args:
            method_name: Name of the hook method to invoke.
            *args: Positional arguments to pass to the hook method.
            **kwargs: Keyword arguments to pass to the hook method.
        """
        for hook in self.hooks:
            try:
                method = getattr(hook, method_name, None)
                if method and callable(method):
                    method(*args, **kwargs)
            except Exception as e:
                self._logger.warning(f"Hook error in {method_name}: {e}")

    def start(self) -> SessionMetadata:
        """Initialize and start the browser session.

        Allocates browser resources, wires together all subsystem components,
        and transitions the session to ACTIVE state.

        Returns:
            SessionMetadata: The initialized session metadata.

        Raises:
            SessionError: If the session is not in INITIALIZING state.
            RuntimeError: If browser initialization fails.
        """
        if self.metadata.state != SessionState.INITIALIZING:
            raise SessionError(
                f"Cannot start session: current state is {self.metadata.state.value}, "
                f"expected INITIALIZING."
            )

        self._session_start_time = time.time()

        try:
            # Initialize browser if not injected
            if self.browser is None:
                self.browser = Browser(config=self._browser_config)

            # Wire up subsystem components
            self.executor = BrowserActionExecutor(self.browser)
            self.memory_manager = self.memory_manager or MemoryManager()
            self.state_manager = BrowserStateMemoryManager(self.browser)
            self.recovery_engine = RecoveryEngine(self.browser)
            self.context_manager = ContextLifecycleManager()

            # Transition to active
            self._transition_state(SessionState.ACTIVE)
            self._dispatch_hook("on_session_start", self.metadata)

            self._logger.info(
                f"Session '{self.metadata.session_id}' started successfully."
            )
            return self.metadata

        except Exception as e:
            self._logger.error(f"Session initialization failed: {e}")
            self.metadata.state = SessionState.ERROR
            self._dispatch_hook("on_error", e, self.metadata)
            raise RuntimeError(f"Session start failed: {e}") from e

    def run_goal(self, goal: str, max_steps: Optional[int] = None) -> GoalResult:
        """Execute a single natural language goal within the active session.

        This is the primary entry point for task execution. The orchestrator
        delegates to BrowserPlanner, handles timeouts, manages memory
        consolidation, and records the goal result.

        Args:
            goal: Natural language description of the browser task to achieve.
            max_steps: Optional override for maximum browser actions.
                Defaults to config.max_actions_per_goal.

        Returns:
            GoalResult: The execution outcome including success status,
                final output, step count, and timing.

        Raises:
            SessionError: If the session is not in ACTIVE state.
        """
        if self.metadata.state != SessionState.ACTIVE:
            raise SessionError(
                f"Cannot run goal: session state is {self.metadata.state.value}, "
                f"expected ACTIVE."
            )

        # Check goal limit
        if self.metadata.goals_submitted >= self.config.max_goals:
            raise SessionError(
                f"Goal limit reached: {self.metadata.goals_submitted}/{self.config.max_goals} "
                f"goals already submitted."
            )

        # Check session timeout
        elapsed = time.time() - self._session_start_time
        if elapsed > self.config.session_timeout_seconds:
            raise SessionError(
                f"Session timeout: {elapsed:.0f}s exceeds limit of "
                f"{self.config.session_timeout_seconds:.0f}s."
            )

        effective_max_steps = max_steps or self.config.max_actions_per_goal
        goal_result = GoalResult(goal=goal)
        goal_result.started_at = time.time()

        # Dispatch goal start event
        self._dispatch_hook("on_goal_start", goal, self.metadata)

        # Set working memory context
        if self.memory_manager:
            self.memory_manager.working.set_goal(goal)

        try:
            # Import planner inline to avoid circular imports
            from tools.browser.planner.planner import BrowserPlanner

            planner = BrowserPlanner(self.browser)
            # Share memory and executor instances
            planner.executor = self.executor
            planner.context_manager = self.context_manager

            planner_result = planner.execute(goal, max_steps=effective_max_steps)

            # Populate goal result from planner output
            goal_result.success = planner_result.success
            goal_result.final_output = planner_result.final_output
            goal_result.steps_taken = planner_result.steps_taken
            goal_result.duration_ms = planner_result.duration_ms
            goal_result.errors = planner_result.errors
            goal_result.report = planner_result.report

        except Exception as e:
            self._logger.error(f"Goal execution error: {e}")
            goal_result.success = False
            goal_result.errors.append(f"Goal execution exception: {e}")
            goal_result.duration_ms = (time.time() - goal_result.started_at) * 1000.0
            self._dispatch_hook("on_error", e, self.metadata)

        goal_result.completed_at = time.time()

        # Update working memory with step results
        if self.memory_manager:
            self.memory_manager.working.log_step(
                action={"action": "goal", "goal": goal},
                success=goal_result.success,
                result_msg=goal_result.final_output or "; ".join(goal_result.errors) or "",
            )

        # Consolidate memory if configured
        if self.config.consolidate_memory_on_goal_complete and self.memory_manager:
            try:
                self.memory_manager.consolidate()
            except Exception as e:
                self._logger.warning(f"Memory consolidation failed: {e}")

        # Record goal result in metadata
        self.metadata.record_goal_result(goal_result)

        # Dispatch goal complete event
        self._dispatch_hook("on_goal_complete", goal_result, self.metadata)

        # Persist checkpoint if configured
        if self.config.persist_session:
            try:
                self.persistence.save_checkpoint(self.metadata, self.config)
            except Exception as e:
                self._logger.warning(f"Checkpoint save failed: {e}")

        return goal_result

    def run_goals(self, goals: List[str], max_steps_per_goal: Optional[int] = None) -> List[GoalResult]:
        """Execute multiple goals sequentially within the active session.

        Args:
            goals: List of natural language goal descriptions.
            max_steps_per_goal: Optional per-goal step limit override.

        Returns:
            List[GoalResult]: Results for each goal in order.

        Raises:
            SessionError: If the session is not in ACTIVE state.
        """
        results = []
        for goal in goals:
            try:
                result = self.run_goal(goal, max_steps=max_steps_per_goal)
                results.append(result)
            except SessionError:
                # Session-level error (timeout, goal limit) — stop processing
                self._logger.warning(f"Session constraint hit, stopping goal queue at '{goal[:60]}'.")
                break
        return results

    def pause(self) -> SessionMetadata:
        """Pause the active session.

        Saves a checkpoint if persistence is enabled. The session can be
        resumed later with ``resume()``.

        Returns:
            SessionMetadata: Session metadata at pause time.

        Raises:
            SessionError: If the session is not in ACTIVE state.
        """
        self._transition_state(SessionState.PAUSED)
        self._dispatch_hook("on_session_pause", self.metadata)

        if self.config.persist_session:
            try:
                self.persistence.save_checkpoint(self.metadata, self.config)
            except Exception as e:
                self._logger.warning(f"Checkpoint save on pause failed: {e}")

        return self.metadata

    def resume(self) -> SessionMetadata:
        """Resume a paused session.

        Returns:
            SessionMetadata: Session metadata after resumption.

        Raises:
            SessionError: If the session is not in PAUSED state.
        """
        self._transition_state(SessionState.ACTIVE)
        self._dispatch_hook("on_session_resume", self.metadata)
        self.metadata.last_activity_at = time.time()
        return self.metadata

    def close(self) -> SessionMetadata:
        """Gracefully close the session and release all resources.

        Performs cleanup: memory consolidation, final checkpoint save,
        browser resource release, and event dispatch.

        Returns:
            SessionMetadata: Final session metadata snapshot.
        """
        current_state = self.metadata.state

        # If already closed, no-op
        if current_state == SessionState.CLOSED:
            return self.metadata

        try:
            # Transition through COMPLETING if coming from ACTIVE
            if current_state == SessionState.ACTIVE:
                self._transition_state(SessionState.COMPLETING)

                # Final memory consolidation
                if self.memory_manager:
                    try:
                        self.memory_manager.consolidate()
                    except Exception as e:
                        self._logger.warning(f"Final memory consolidation failed: {e}")

            # Transition to CLOSED from any valid predecessor state
            if self.metadata.state in (
                SessionState.COMPLETING,
                SessionState.PAUSED,
                SessionState.ERROR,
                SessionState.INITIALIZING,
            ):
                self._transition_state(SessionState.CLOSED)

        except SessionError:
            # Force close if transition fails
            self.metadata.state = SessionState.CLOSED

        # Save final checkpoint
        if self.config.persist_session:
            try:
                self.persistence.save_checkpoint(self.metadata, self.config)
            except Exception as e:
                self._logger.warning(f"Final checkpoint save failed: {e}")

        # Cleanup browser resources
        if self.config.cleanup_on_close and self.browser:
            try:
                self.browser.close()
            except Exception as e:
                self._logger.warning(f"Browser cleanup failed: {e}")

        self._dispatch_hook("on_session_close", self.metadata)

        self._logger.info(
            f"Session '{self.metadata.session_id}' closed. "
            f"Goals: {self.metadata.goals_completed}/{self.metadata.goals_submitted}"
        )
        return self.metadata

    @classmethod
    def restore_session(
        cls,
        session_id: str,
        persist_directory: str = ".browser_artifacts/sessions",
        browser: Optional[Browser] = None,
        hooks: Optional[List[SessionHook]] = None,
    ) -> "SessionOrchestrator":
        """Restore a previously saved session from a checkpoint file.

        Creates a new SessionOrchestrator instance with the metadata and
        configuration restored from disk. The session starts in PAUSED state
        and must be ``resume()``d before new goals can be executed.

        Args:
            session_id: The session_id to restore.
            persist_directory: Directory containing checkpoint files.
            browser: Optional Browser instance to use (a new one is created if None).
            hooks: Optional list of SessionHook observers.

        Returns:
            SessionOrchestrator: A new orchestrator with restored state.

        Raises:
            SessionError: If no checkpoint exists for the given session_id.
        """
        persistence = SessionPersistence(persist_directory)
        checkpoint_data = persistence.load_checkpoint(session_id)

        if checkpoint_data is None:
            raise SessionError(f"No checkpoint found for session '{session_id}'")

        config = persistence.restore_config(checkpoint_data)
        metadata = persistence.restore_metadata(checkpoint_data)

        orchestrator = cls(config=config, browser=browser, hooks=hooks)
        orchestrator.metadata = metadata
        orchestrator.persistence = persistence

        # Initialize subsystems
        if orchestrator.browser is None:
            orchestrator.browser = Browser(
                config=BrowserConfig(engine_type=BrowserEngineType.PLAYWRIGHT)
            )
        orchestrator.executor = BrowserActionExecutor(orchestrator.browser)
        orchestrator.memory_manager = MemoryManager()
        orchestrator.state_manager = BrowserStateMemoryManager(orchestrator.browser)
        orchestrator.recovery_engine = RecoveryEngine(orchestrator.browser)
        orchestrator.context_manager = ContextLifecycleManager()

        logger.info(f"Session '{session_id}' restored from checkpoint (state: PAUSED).")
        return orchestrator

    def get_session_summary(self) -> Dict[str, Any]:
        """Get a comprehensive session summary dictionary.

        Returns:
            Dict[str, Any]: Session metadata, status, and performance metrics.
        """
        return {
            **self.metadata.to_dict(),
            "elapsed_since_start_ms": (
                (time.time() - self._session_start_time) * 1000.0
                if self._session_start_time > 0
                else 0.0
            ),
        }

    def add_hook(self, hook: SessionHook) -> None:
        """Register a new session event hook.

        Args:
            hook: SessionHook instance to register.
        """
        self.hooks.append(hook)

    def remove_hook(self, hook: SessionHook) -> None:
        """Unregister a session event hook.

        Args:
            hook: SessionHook instance to remove.
        """
        if hook in self.hooks:
            self.hooks.remove(hook)
