"""Comprehensive tests for the Session Orchestrator component.

Tests session lifecycle, multi-goal execution, pause/resume, persistence,
hooks, error handling, and edge cases.
"""

import json
import os
import shutil
import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from tools.browser.session.models import (
    GoalResult,
    SessionConfig,
    SessionMetadata,
    SessionState,
)
from tools.browser.session.hooks import LoggingHook, MetricsHook, SessionHook
from tools.browser.session.persistence import SessionPersistence
from tools.browser.session.orchestrator import SessionOrchestrator, SessionError


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

TEST_PERSIST_DIR = ".browser_artifacts/test_sessions"


@pytest.fixture
def mock_browser():
    """Create a mock Browser instance."""
    browser = MagicMock()
    browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com")
    browser.get_page_title.return_value = MagicMock(success=True, data="Example")
    browser.get_page_html.return_value = MagicMock(success=True, data="<html></html>")
    browser.capture_screenshot.return_value = MagicMock(success=True, data={"screenshot_path": ""})
    browser.execute_javascript.return_value = MagicMock(success=True, data="")
    browser.close.return_value = None
    return browser


@pytest.fixture
def session_config():
    """Create a test session config."""
    return SessionConfig(
        max_goals=5,
        goal_timeout_seconds=10.0,
        session_timeout_seconds=60.0,
        max_actions_per_goal=5,
        persist_session=False,
        persist_directory=TEST_PERSIST_DIR,
    )


@pytest.fixture
def orchestrator(mock_browser, session_config):
    """Create a session orchestrator with mocked browser."""
    orch = SessionOrchestrator(
        config=session_config,
        browser=mock_browser,
        hooks=[LoggingHook()],
    )
    return orch


@pytest.fixture(autouse=True)
def cleanup_test_dir():
    """Cleanup test persistence directory after each test."""
    yield
    if os.path.exists(TEST_PERSIST_DIR):
        shutil.rmtree(TEST_PERSIST_DIR, ignore_errors=True)


# ─────────────────────────────────────────────
# Session Models Tests
# ─────────────────────────────────────────────

class TestSessionModels:
    """Tests for session data models."""

    def test_session_state_values(self):
        """All session states should have correct string values."""
        assert SessionState.INITIALIZING.value == "INITIALIZING"
        assert SessionState.ACTIVE.value == "ACTIVE"
        assert SessionState.PAUSED.value == "PAUSED"
        assert SessionState.COMPLETING.value == "COMPLETING"
        assert SessionState.CLOSED.value == "CLOSED"
        assert SessionState.ERROR.value == "ERROR"

    def test_session_config_defaults(self):
        """SessionConfig should have sensible defaults."""
        config = SessionConfig()
        assert config.max_goals == 50
        assert config.goal_timeout_seconds == 300.0
        assert config.max_actions_per_goal == 25
        assert config.persist_session is False
        assert config.cleanup_on_close is True

    def test_goal_result_serialization(self):
        """GoalResult should serialize to dictionary correctly."""
        result = GoalResult(
            goal="Test goal",
            success=True,
            final_output="Answer",
            steps_taken=3,
            duration_ms=1500.0,
        )
        d = result.to_dict()
        assert d["goal"] == "Test goal"
        assert d["success"] is True
        assert d["final_output"] == "Answer"
        assert d["steps_taken"] == 3
        assert d["duration_ms"] == 1500.0

    def test_session_metadata_record_goal(self):
        """SessionMetadata should correctly aggregate goal results."""
        meta = SessionMetadata()
        
        # Record a success
        result_ok = GoalResult(goal="g1", success=True, steps_taken=5, duration_ms=1000.0)
        meta.record_goal_result(result_ok)
        
        assert meta.goals_submitted == 1
        assert meta.goals_completed == 1
        assert meta.goals_failed == 0
        assert meta.total_actions == 5
        assert meta.total_duration_ms == 1000.0

        # Record a failure
        result_fail = GoalResult(goal="g2", success=False, steps_taken=3, duration_ms=500.0)
        meta.record_goal_result(result_fail)

        assert meta.goals_submitted == 2
        assert meta.goals_completed == 1
        assert meta.goals_failed == 1
        assert meta.total_actions == 8
        assert meta.get_success_rate() == 50.0

    def test_session_metadata_to_dict(self):
        """SessionMetadata should serialize completely."""
        meta = SessionMetadata()
        d = meta.to_dict()
        assert "session_id" in d
        assert "state" in d
        assert "success_rate_pct" in d
        assert "goal_results" in d

    def test_success_rate_zero_goals(self):
        """Success rate should be 0.0 when no goals are submitted."""
        meta = SessionMetadata()
        assert meta.get_success_rate() == 0.0


# ─────────────────────────────────────────────
# Session Hooks Tests
# ─────────────────────────────────────────────

class TestSessionHooks:
    """Tests for session lifecycle hooks."""

    def test_metrics_hook_goal_tracking(self):
        """MetricsHook should accurately track goal outcomes."""
        hook = MetricsHook()
        meta = SessionMetadata()
        
        hook.on_session_start(meta)
        assert hook.metrics["sessions_started"] == 1
        
        hook.on_goal_start("goal1", meta)
        assert hook.metrics["goals_started"] == 1

        result = GoalResult(success=True, steps_taken=5, duration_ms=1200.0)
        hook.on_goal_complete(result, meta)
        
        assert hook.metrics["goals_succeeded"] == 1
        assert hook.metrics["total_actions"] == 5
        
        summary = hook.get_summary()
        assert summary["success_rate_pct"] == 100.0
        assert summary["avg_goal_duration_ms"] == 1200.0

    def test_metrics_hook_error_counting(self):
        """MetricsHook should count errors."""
        hook = MetricsHook()
        meta = SessionMetadata()
        
        hook.on_error(ValueError("test"), meta)
        assert hook.metrics["errors_count"] == 1

    def test_custom_hook_receives_events(self):
        """Custom hooks should receive all lifecycle events."""
        events_received = []

        class TrackingHook(SessionHook):
            def on_session_start(self, metadata):
                events_received.append("start")
            def on_goal_start(self, goal, metadata):
                events_received.append(f"goal:{goal}")
            def on_session_close(self, metadata):
                events_received.append("close")

        hook = TrackingHook()
        meta = SessionMetadata()
        
        hook.on_session_start(meta)
        hook.on_goal_start("test_goal", meta)
        hook.on_session_close(meta)
        
        assert events_received == ["start", "goal:test_goal", "close"]


# ─────────────────────────────────────────────
# Session Persistence Tests
# ─────────────────────────────────────────────

class TestSessionPersistence:
    """Tests for session checkpoint save/load."""

    def test_save_and_load_checkpoint(self):
        """Should save and load checkpoint successfully."""
        persistence = SessionPersistence(TEST_PERSIST_DIR)
        config = SessionConfig(max_goals=10)
        meta = SessionMetadata(session_id="test_session_001")
        meta.state = SessionState.ACTIVE

        result = GoalResult(goal="search", success=True, steps_taken=3, duration_ms=500.0)
        meta.record_goal_result(result)

        # Save
        path = persistence.save_checkpoint(meta, config)
        assert os.path.exists(path)

        # Load
        data = persistence.load_checkpoint("test_session_001")
        assert data is not None
        assert data["metadata"]["session_id"] == "test_session_001"
        assert len(data["metadata"]["goal_results"]) == 1

    def test_restore_metadata(self):
        """Should restore SessionMetadata from checkpoint data."""
        persistence = SessionPersistence(TEST_PERSIST_DIR)
        config = SessionConfig()
        meta = SessionMetadata(session_id="restore_test")
        meta.record_goal_result(GoalResult(goal="g1", success=True, steps_taken=2, duration_ms=300.0))
        
        persistence.save_checkpoint(meta, config)
        data = persistence.load_checkpoint("restore_test")
        
        restored = persistence.restore_metadata(data)
        assert restored.session_id == "restore_test"
        assert restored.state == SessionState.PAUSED  # Restored sessions start paused
        assert restored.goals_submitted == 1
        assert len(restored.goal_results) == 1

    def test_restore_config(self):
        """Should restore SessionConfig from checkpoint data."""
        persistence = SessionPersistence(TEST_PERSIST_DIR)
        config = SessionConfig(max_goals=42, goal_timeout_seconds=99.0)
        meta = SessionMetadata(session_id="cfg_test")
        
        persistence.save_checkpoint(meta, config)
        data = persistence.load_checkpoint("cfg_test")
        
        restored_cfg = persistence.restore_config(data)
        assert restored_cfg.max_goals == 42
        assert restored_cfg.goal_timeout_seconds == 99.0

    def test_delete_checkpoint(self):
        """Should delete checkpoint file."""
        persistence = SessionPersistence(TEST_PERSIST_DIR)
        meta = SessionMetadata(session_id="delete_me")
        persistence.save_checkpoint(meta, SessionConfig())
        
        assert persistence.delete_checkpoint("delete_me") is True
        assert persistence.load_checkpoint("delete_me") is None

    def test_load_nonexistent_checkpoint(self):
        """Loading a nonexistent checkpoint should return None."""
        persistence = SessionPersistence(TEST_PERSIST_DIR)
        assert persistence.load_checkpoint("nonexistent") is None

    def test_list_sessions(self):
        """Should list all saved sessions."""
        persistence = SessionPersistence(TEST_PERSIST_DIR)
        
        for sid in ["sess_a", "sess_b", "sess_c"]:
            meta = SessionMetadata(session_id=sid)
            persistence.save_checkpoint(meta, SessionConfig())
        
        sessions = persistence.list_sessions()
        assert len(sessions) == 3
        assert "sess_a" in sessions


# ─────────────────────────────────────────────
# Session Orchestrator Tests
# ─────────────────────────────────────────────

class TestSessionOrchestrator:
    """Tests for the main SessionOrchestrator."""

    def test_start_transitions_to_active(self, orchestrator):
        """Starting a session should transition to ACTIVE state."""
        assert orchestrator.metadata.state == SessionState.INITIALIZING
        orchestrator.start()
        assert orchestrator.metadata.state == SessionState.ACTIVE

    def test_start_initializes_subsystems(self, orchestrator):
        """Starting should initialize all subsystem components."""
        orchestrator.start()
        assert orchestrator.executor is not None
        assert orchestrator.memory_manager is not None
        assert orchestrator.state_manager is not None
        assert orchestrator.recovery_engine is not None
        assert orchestrator.context_manager is not None

    def test_start_dispatches_hook(self, orchestrator):
        """Starting should dispatch on_session_start to hooks."""
        hook = MetricsHook()
        orchestrator.add_hook(hook)
        orchestrator.start()
        assert hook.metrics["sessions_started"] == 1

    def test_double_start_raises(self, orchestrator):
        """Starting an already active session should raise SessionError."""
        orchestrator.start()
        with pytest.raises(SessionError, match="Cannot start session"):
            orchestrator.start()

    def test_run_goal_basic(self, orchestrator):
        """Running a goal should return a GoalResult."""
        orchestrator.start()
        
        # Mock the planner to avoid actual LLM calls
        with patch("tools.browser.planner.planner.BrowserPlanner") as MockPlanner:
            mock_planner_instance = MagicMock()
            mock_planner_instance.execute.return_value = MagicMock(
                success=True,
                final_output="Test result",
                steps_taken=3,
                duration_ms=1000.0,
                errors=[],
                report=None,
            )
            MockPlanner.return_value = mock_planner_instance
            
            result = orchestrator.run_goal("Search for Python tutorials")
        
        assert result.success is True
        assert result.final_output == "Test result"
        assert result.steps_taken == 3
        assert orchestrator.metadata.goals_submitted == 1
        assert orchestrator.metadata.goals_completed == 1

    def test_run_goal_failure(self, orchestrator):
        """Failed goals should be tracked correctly."""
        orchestrator.start()
        
        with patch("tools.browser.planner.planner.BrowserPlanner") as MockPlanner:
            mock_planner_instance = MagicMock()
            mock_planner_instance.execute.return_value = MagicMock(
                success=False,
                final_output=None,
                steps_taken=5,
                duration_ms=2000.0,
                errors=["Budget exceeded"],
                report=None,
            )
            MockPlanner.return_value = mock_planner_instance
            
            result = orchestrator.run_goal("Impossible task")
        
        assert result.success is False
        assert orchestrator.metadata.goals_failed == 1

    def test_run_goals_multiple(self, orchestrator):
        """Running multiple goals should track all results."""
        orchestrator.start()
        
        with patch("tools.browser.planner.planner.BrowserPlanner") as MockPlanner:
            mock_planner_instance = MagicMock()
            mock_planner_instance.execute.return_value = MagicMock(
                success=True,
                final_output="Done",
                steps_taken=2,
                duration_ms=500.0,
                errors=[],
                report=None,
            )
            MockPlanner.return_value = mock_planner_instance
            
            results = orchestrator.run_goals(["Goal A", "Goal B", "Goal C"])
        
        assert len(results) == 3
        assert orchestrator.metadata.goals_submitted == 3
        assert orchestrator.metadata.goals_completed == 3

    def test_run_goal_not_active_raises(self, orchestrator):
        """Running a goal on non-ACTIVE session should raise SessionError."""
        with pytest.raises(SessionError, match="Cannot run goal"):
            orchestrator.run_goal("test")

    def test_goal_limit_enforcement(self, orchestrator):
        """Should raise SessionError when goal limit is reached."""
        orchestrator.config.max_goals = 1
        orchestrator.start()
        
        with patch("tools.browser.planner.planner.BrowserPlanner") as MockPlanner:
            mock_planner_instance = MagicMock()
            mock_planner_instance.execute.return_value = MagicMock(
                success=True, final_output="Ok", steps_taken=1,
                duration_ms=100.0, errors=[], report=None,
            )
            MockPlanner.return_value = mock_planner_instance
            
            orchestrator.run_goal("Goal 1")
            
            with pytest.raises(SessionError, match="Goal limit reached"):
                orchestrator.run_goal("Goal 2")

    def test_pause_and_resume(self, orchestrator):
        """Session should pause and resume correctly."""
        orchestrator.start()
        assert orchestrator.metadata.state == SessionState.ACTIVE
        
        orchestrator.pause()
        assert orchestrator.metadata.state == SessionState.PAUSED
        
        orchestrator.resume()
        assert orchestrator.metadata.state == SessionState.ACTIVE

    def test_pause_not_active_raises(self, orchestrator):
        """Pausing a non-ACTIVE session should raise SessionError."""
        with pytest.raises(SessionError):
            orchestrator.pause()

    def test_close_from_active(self, orchestrator):
        """Closing from ACTIVE should go through COMPLETING → CLOSED."""
        orchestrator.start()
        meta = orchestrator.close()
        assert meta.state == SessionState.CLOSED

    def test_close_from_paused(self, orchestrator):
        """Closing from PAUSED should go directly to CLOSED."""
        orchestrator.start()
        orchestrator.pause()
        meta = orchestrator.close()
        assert meta.state == SessionState.CLOSED

    def test_close_calls_browser_cleanup(self, orchestrator, mock_browser):
        """Closing should call browser.close() for resource cleanup."""
        orchestrator.start()
        orchestrator.close()
        mock_browser.close.assert_called_once()

    def test_close_idempotent(self, orchestrator):
        """Closing an already closed session should be a no-op."""
        orchestrator.start()
        orchestrator.close()
        meta = orchestrator.close()  # Second close
        assert meta.state == SessionState.CLOSED

    def test_get_session_summary(self, orchestrator):
        """Session summary should contain key fields."""
        orchestrator.start()
        summary = orchestrator.get_session_summary()
        assert "session_id" in summary
        assert "state" in summary
        assert "elapsed_since_start_ms" in summary

    def test_hook_management(self, orchestrator):
        """Should add and remove hooks."""
        hook = MetricsHook()
        orchestrator.add_hook(hook)
        assert hook in orchestrator.hooks
        
        orchestrator.remove_hook(hook)
        assert hook not in orchestrator.hooks

    def test_goal_with_exception(self, orchestrator):
        """Goals that throw exceptions should be captured gracefully."""
        orchestrator.start()
        
        with patch("tools.browser.planner.planner.BrowserPlanner") as MockPlanner:
            mock_planner_instance = MagicMock()
            mock_planner_instance.execute.side_effect = RuntimeError("LLM timeout")
            MockPlanner.return_value = mock_planner_instance
            
            result = orchestrator.run_goal("Crashing goal")
        
        assert result.success is False
        assert "LLM timeout" in result.errors[0]
        assert orchestrator.metadata.goals_failed == 1


# ─────────────────────────────────────────────
# Persistence Integration Tests
# ─────────────────────────────────────────────

class TestPersistenceIntegration:
    """Tests for session persistence integration with orchestrator."""

    def test_persistence_on_goal_complete(self, mock_browser):
        """With persist_session=True, checkpoints should be saved after goals."""
        config = SessionConfig(
            max_goals=5,
            persist_session=True,
            persist_directory=TEST_PERSIST_DIR,
        )
        orch = SessionOrchestrator(config=config, browser=mock_browser, hooks=[])
        orch.start()
        
        with patch("tools.browser.planner.planner.BrowserPlanner") as MockPlanner:
            mock_planner_instance = MagicMock()
            mock_planner_instance.execute.return_value = MagicMock(
                success=True, final_output="Done", steps_taken=2,
                duration_ms=500.0, errors=[], report=None,
            )
            MockPlanner.return_value = mock_planner_instance
            orch.run_goal("Persisted goal")
        
        # Checkpoint should exist
        sessions = orch.persistence.list_sessions()
        assert len(sessions) >= 1
        
        orch.close()


# ─────────────────────────────────────────────
# End-to-End Scenario Tests
# ─────────────────────────────────────────────

class TestEndToEndScenarios:
    """Realistic scenario tests."""

    def test_multi_goal_research_session(self, mock_browser):
        """Simulate a multi-goal research session."""
        config = SessionConfig(max_goals=10, max_actions_per_goal=10)
        orch = SessionOrchestrator(config=config, browser=mock_browser, hooks=[MetricsHook()])
        orch.start()
        
        goals = [
            "Search for AI research papers on Google Scholar",
            "Extract the top 3 results",
            "Summarize the findings",
        ]
        
        with patch("tools.browser.planner.planner.BrowserPlanner") as MockPlanner:
            mock_planner_instance = MagicMock()
            call_count = [0]
            def mock_execute(goal, max_steps=15):
                call_count[0] += 1
                return MagicMock(
                    success=True, final_output=f"Result {call_count[0]}",
                    steps_taken=call_count[0] + 1, duration_ms=500.0 * call_count[0],
                    errors=[], report=None,
                )
            mock_planner_instance.execute.side_effect = mock_execute
            MockPlanner.return_value = mock_planner_instance
            
            results = orch.run_goals(goals)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert orch.metadata.goals_completed == 3
        assert orch.metadata.total_actions == (2 + 3 + 4)
        
        summary = orch.get_session_summary()
        assert summary["goals_completed"] == 3
        
        orch.close()
        assert orch.metadata.state == SessionState.CLOSED

    def test_session_with_mixed_results(self, mock_browser):
        """Simulate a session where some goals succeed and some fail."""
        config = SessionConfig(max_goals=5)
        hook = MetricsHook()
        orch = SessionOrchestrator(config=config, browser=mock_browser, hooks=[hook])
        orch.start()
        
        with patch("tools.browser.planner.planner.BrowserPlanner") as MockPlanner:
            mock_planner_instance = MagicMock()
            call_count = [0]
            def mock_execute(goal, max_steps=25):
                call_count[0] += 1
                success = call_count[0] % 2 == 1  # Odd goals succeed
                return MagicMock(
                    success=success, final_output="Ok" if success else None,
                    steps_taken=3, duration_ms=1000.0,
                    errors=[] if success else ["Failed"], report=None,
                )
            mock_planner_instance.execute.side_effect = mock_execute
            MockPlanner.return_value = mock_planner_instance
            
            for i in range(4):
                orch.run_goal(f"Goal {i+1}")
        
        assert orch.metadata.goals_completed == 2
        assert orch.metadata.goals_failed == 2
        assert orch.metadata.get_success_rate() == 50.0
        
        summary = hook.get_summary()
        assert summary["goals_succeeded"] == 2
        assert summary["goals_failed"] == 2
        
        orch.close()
