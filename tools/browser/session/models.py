"""Session Orchestrator Data Models.

Defines configuration, state, metadata, and result types for
the browser agent session lifecycle.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SessionState(str, Enum):
    """Lifecycle state of a browser agent session.

    States:
        INITIALIZING: Session is being set up (browser launch, component wiring).
        ACTIVE: Session is executing goals.
        PAUSED: Session is temporarily suspended; can be resumed.
        COMPLETING: Session is running cleanup (memory consolidation, report generation).
        CLOSED: Session has terminated normally.
        ERROR: Session has terminated due to an unrecoverable error.
    """

    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETING = "COMPLETING"
    CLOSED = "CLOSED"
    ERROR = "ERROR"


@dataclass
class SessionConfig:
    """Configuration parameters for a browser agent session.

    Attributes:
        max_goals: Maximum number of goals that can be executed in a single session.
        goal_timeout_seconds: Per-goal execution timeout in seconds.
        session_timeout_seconds: Total session timeout in seconds.
        max_actions_per_goal: Maximum browser actions allowed per goal.
        persist_session: Whether to save session checkpoints to disk.
        persist_directory: Directory for session checkpoint files.
        consolidate_memory_on_goal_complete: Whether to consolidate working memory
            into long-term storage after each goal completes.
        auto_screenshot_on_goal_complete: Capture a screenshot after each goal finishes.
        cleanup_on_close: Whether to close the browser and release resources on session close.
    """

    max_goals: int = 50
    goal_timeout_seconds: float = 300.0
    session_timeout_seconds: float = 3600.0
    max_actions_per_goal: int = 25
    persist_session: bool = False
    persist_directory: str = ".browser_artifacts/sessions"
    consolidate_memory_on_goal_complete: bool = True
    auto_screenshot_on_goal_complete: bool = False
    cleanup_on_close: bool = True


@dataclass
class GoalResult:
    """Outcome of a single goal execution within a session.

    Attributes:
        goal_id: Unique identifier for this goal execution.
        goal: Natural language goal description.
        success: Whether the goal was achieved.
        final_output: The answer or extracted data, if any.
        steps_taken: Number of browser actions executed.
        duration_ms: Wall-clock execution time in milliseconds.
        errors: List of error messages encountered.
        report: Optional serialized execution report dictionary.
        started_at: Unix timestamp when goal execution began.
        completed_at: Unix timestamp when goal execution ended.
    """

    goal_id: str = field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    goal: str = ""
    success: bool = False
    final_output: Optional[str] = None
    steps_taken: int = 0
    duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    report: Optional[Dict[str, Any]] = None
    started_at: float = 0.0
    completed_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize goal result to a JSON-compatible dictionary."""
        return {
            "goal_id": self.goal_id,
            "goal": self.goal,
            "success": self.success,
            "final_output": self.final_output,
            "steps_taken": self.steps_taken,
            "duration_ms": round(self.duration_ms, 2),
            "errors": self.errors,
            "report": self.report,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class SessionMetadata:
    """Aggregate tracking metadata for a full browser session.

    Attributes:
        session_id: Unique session identifier.
        state: Current session lifecycle state.
        created_at: Unix timestamp of session creation.
        last_activity_at: Unix timestamp of last goal/action activity.
        goals_submitted: Total number of goals submitted.
        goals_completed: Number of goals that completed successfully.
        goals_failed: Number of goals that failed.
        total_actions: Cumulative browser actions across all goals.
        total_duration_ms: Cumulative wall-clock time across all goals.
        goal_results: Ordered list of per-goal results.
    """

    session_id: str = field(default_factory=lambda: f"session_{uuid.uuid4().hex[:12]}")
    state: SessionState = SessionState.INITIALIZING
    created_at: float = field(default_factory=time.time)
    last_activity_at: float = field(default_factory=time.time)
    goals_submitted: int = 0
    goals_completed: int = 0
    goals_failed: int = 0
    total_actions: int = 0
    total_duration_ms: float = 0.0
    goal_results: List[GoalResult] = field(default_factory=list)

    def record_goal_result(self, result: GoalResult) -> None:
        """Register a completed goal result and update aggregate counters.

        Args:
            result: The completed GoalResult instance.
        """
        self.goal_results.append(result)
        self.goals_submitted += 1
        self.total_actions += result.steps_taken
        self.total_duration_ms += result.duration_ms
        self.last_activity_at = time.time()

        if result.success:
            self.goals_completed += 1
        else:
            self.goals_failed += 1

    def get_success_rate(self) -> float:
        """Calculate the session goal success rate as a percentage.

        Returns:
            float: Success percentage (0.0-100.0), or 0.0 if no goals submitted.
        """
        if self.goals_submitted == 0:
            return 0.0
        return (self.goals_completed / self.goals_submitted) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session metadata to a JSON-compatible dictionary."""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "created_at": self.created_at,
            "last_activity_at": self.last_activity_at,
            "goals_submitted": self.goals_submitted,
            "goals_completed": self.goals_completed,
            "goals_failed": self.goals_failed,
            "total_actions": self.total_actions,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "success_rate_pct": round(self.get_success_rate(), 1),
            "goal_results": [r.to_dict() for r in self.goal_results],
        }
