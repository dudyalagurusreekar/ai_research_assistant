"""Session Event Hooks for extensible lifecycle observation.

Provides an abstract hook interface and concrete implementations for
logging, metrics, and custom event handling throughout the session lifecycle.
"""

import abc
import logging
from typing import Any, Dict

from tools.browser.session.models import GoalResult, SessionMetadata, SessionState

logger = logging.getLogger("SessionHooks")


class SessionHook(abc.ABC):
    """Abstract base class for session lifecycle event observers.

    Subclass this to tap into session events for logging, metrics,
    alerting, or any custom side-effect processing. All methods are
    optional no-ops by default so subclasses only override what they need.
    """

    def on_session_start(self, metadata: SessionMetadata) -> None:
        """Called when the session transitions to ACTIVE state.

        Args:
            metadata: Current session metadata snapshot.
        """

    def on_session_pause(self, metadata: SessionMetadata) -> None:
        """Called when the session is paused.

        Args:
            metadata: Current session metadata snapshot.
        """

    def on_session_resume(self, metadata: SessionMetadata) -> None:
        """Called when the session resumes from PAUSED state.

        Args:
            metadata: Current session metadata snapshot.
        """

    def on_session_close(self, metadata: SessionMetadata) -> None:
        """Called when the session closes (normally or due to error).

        Args:
            metadata: Final session metadata snapshot.
        """

    def on_goal_start(self, goal: str, metadata: SessionMetadata) -> None:
        """Called when a new goal begins execution.

        Args:
            goal: Natural language goal description.
            metadata: Current session metadata snapshot.
        """

    def on_goal_complete(self, result: GoalResult, metadata: SessionMetadata) -> None:
        """Called when a goal finishes execution (success or failure).

        Args:
            result: The completed goal result.
            metadata: Current session metadata snapshot.
        """

    def on_state_change(
        self, old_state: SessionState, new_state: SessionState, metadata: SessionMetadata
    ) -> None:
        """Called on every session state transition.

        Args:
            old_state: Previous session state.
            new_state: New session state.
            metadata: Current session metadata snapshot.
        """

    def on_error(self, error: Exception, metadata: SessionMetadata) -> None:
        """Called when an error occurs during session execution.

        Args:
            error: The exception that was raised.
            metadata: Current session metadata snapshot.
        """


class LoggingHook(SessionHook):
    """Default hook that logs all session lifecycle events at INFO level.

    Provides human-readable log messages for debugging and operational
    monitoring of browser agent sessions.
    """

    def __init__(self, log_level: int = logging.INFO) -> None:
        """Initialize the logging hook.

        Args:
            log_level: Python logging level for event messages.
        """
        self._logger = logging.getLogger("SessionLifecycle")
        self._log_level = log_level

    def on_session_start(self, metadata: SessionMetadata) -> None:
        """Log session start event."""
        self._logger.log(
            self._log_level,
            f"Session '{metadata.session_id}' started.",
        )

    def on_session_pause(self, metadata: SessionMetadata) -> None:
        """Log session pause event."""
        self._logger.log(
            self._log_level,
            f"Session '{metadata.session_id}' paused after {metadata.goals_submitted} goals.",
        )

    def on_session_resume(self, metadata: SessionMetadata) -> None:
        """Log session resume event."""
        self._logger.log(
            self._log_level,
            f"Session '{metadata.session_id}' resumed.",
        )

    def on_session_close(self, metadata: SessionMetadata) -> None:
        """Log session close event with summary statistics."""
        self._logger.log(
            self._log_level,
            f"Session '{metadata.session_id}' closed. "
            f"Goals: {metadata.goals_completed}/{metadata.goals_submitted} succeeded "
            f"({metadata.get_success_rate():.1f}%), "
            f"Total actions: {metadata.total_actions}, "
            f"Duration: {metadata.total_duration_ms:.0f}ms.",
        )

    def on_goal_start(self, goal: str, metadata: SessionMetadata) -> None:
        """Log goal start event."""
        self._logger.log(
            self._log_level,
            f"[{metadata.session_id}] Goal #{metadata.goals_submitted + 1} started: '{goal[:80]}'",
        )

    def on_goal_complete(self, result: GoalResult, metadata: SessionMetadata) -> None:
        """Log goal completion event with outcome."""
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        self._logger.log(
            self._log_level,
            f"[{metadata.session_id}] Goal '{result.goal[:60]}' {status} "
            f"in {result.steps_taken} steps ({result.duration_ms:.0f}ms).",
        )

    def on_state_change(
        self, old_state: SessionState, new_state: SessionState, metadata: SessionMetadata
    ) -> None:
        """Log state transition."""
        self._logger.log(
            logging.DEBUG,
            f"[{metadata.session_id}] State transition: {old_state.value} → {new_state.value}",
        )

    def on_error(self, error: Exception, metadata: SessionMetadata) -> None:
        """Log error event."""
        self._logger.error(
            f"[{metadata.session_id}] Error: {type(error).__name__}: {error}",
        )


class MetricsHook(SessionHook):
    """Hook that collects quantitative performance metrics from session events.

    Stores timing, throughput, and error-rate data for operational dashboards
    and performance analysis.
    """

    def __init__(self) -> None:
        """Initialize metrics collection."""
        self.metrics: Dict[str, Any] = {
            "sessions_started": 0,
            "sessions_closed": 0,
            "goals_started": 0,
            "goals_succeeded": 0,
            "goals_failed": 0,
            "total_actions": 0,
            "total_goal_duration_ms": 0.0,
            "errors_count": 0,
            "goal_durations_ms": [],
        }

    def on_session_start(self, metadata: SessionMetadata) -> None:
        """Increment sessions started counter."""
        self.metrics["sessions_started"] += 1

    def on_session_close(self, metadata: SessionMetadata) -> None:
        """Increment sessions closed counter."""
        self.metrics["sessions_closed"] += 1

    def on_goal_start(self, goal: str, metadata: SessionMetadata) -> None:
        """Increment goals started counter."""
        self.metrics["goals_started"] += 1

    def on_goal_complete(self, result: GoalResult, metadata: SessionMetadata) -> None:
        """Record goal completion metrics."""
        if result.success:
            self.metrics["goals_succeeded"] += 1
        else:
            self.metrics["goals_failed"] += 1
        self.metrics["total_actions"] += result.steps_taken
        self.metrics["total_goal_duration_ms"] += result.duration_ms
        self.metrics["goal_durations_ms"].append(result.duration_ms)

    def on_error(self, error: Exception, metadata: SessionMetadata) -> None:
        """Increment error counter."""
        self.metrics["errors_count"] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary dictionary of collected metrics.

        Returns:
            Dict containing aggregate metrics with averages and rates.
        """
        durations = self.metrics["goal_durations_ms"]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        total_goals = self.metrics["goals_succeeded"] + self.metrics["goals_failed"]
        success_rate = (
            (self.metrics["goals_succeeded"] / total_goals * 100.0)
            if total_goals > 0
            else 0.0
        )

        return {
            **self.metrics,
            "avg_goal_duration_ms": round(avg_duration, 2),
            "success_rate_pct": round(success_rate, 1),
        }
