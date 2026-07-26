"""Session Persistence Layer.

Handles saving and loading session checkpoints to disk for crash recovery
and session resumption. Uses JSON serialization for portability.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from tools.browser.session.models import (
    GoalResult,
    SessionConfig,
    SessionMetadata,
    SessionState,
)

logger = logging.getLogger("SessionPersistence")


class SessionPersistence:
    """Manages session checkpoint save/load operations for crash recovery.

    Stores session metadata, goal results, and configuration as JSON files
    in a configurable directory. Each session gets its own checkpoint file
    keyed by session_id.

    Attributes:
        persist_directory: Absolute path to the checkpoint storage directory.
    """

    def __init__(self, persist_directory: str = ".browser_artifacts/sessions") -> None:
        """Initialize the persistence layer.

        Args:
            persist_directory: Directory path for checkpoint files.
                Created automatically if it does not exist.
        """
        self.persist_directory = os.path.abspath(persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        self._logger = logger

    def _checkpoint_path(self, session_id: str) -> str:
        """Compute the filesystem path for a session checkpoint file.

        Args:
            session_id: Unique session identifier.

        Returns:
            str: Absolute path to the checkpoint JSON file.
        """
        safe_id = session_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.persist_directory, f"{safe_id}.checkpoint.json")

    def save_checkpoint(
        self,
        metadata: SessionMetadata,
        config: SessionConfig,
    ) -> str:
        """Write a session checkpoint to disk.

        Atomically writes the checkpoint by first writing to a temporary file,
        then renaming to the final path. This prevents corruption from partial writes.

        Args:
            metadata: Current session metadata to persist.
            config: Session configuration to persist.

        Returns:
            str: Path to the saved checkpoint file.

        Raises:
            IOError: If the checkpoint file cannot be written.
        """
        checkpoint_path = self._checkpoint_path(metadata.session_id)
        tmp_path = checkpoint_path + ".tmp"

        checkpoint_data: Dict[str, Any] = {
            "version": 1,
            "saved_at": time.time(),
            "metadata": metadata.to_dict(),
            "config": {
                "max_goals": config.max_goals,
                "goal_timeout_seconds": config.goal_timeout_seconds,
                "session_timeout_seconds": config.session_timeout_seconds,
                "max_actions_per_goal": config.max_actions_per_goal,
                "persist_session": config.persist_session,
                "persist_directory": config.persist_directory,
                "consolidate_memory_on_goal_complete": config.consolidate_memory_on_goal_complete,
                "auto_screenshot_on_goal_complete": config.auto_screenshot_on_goal_complete,
                "cleanup_on_close": config.cleanup_on_close,
            },
        }

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, default=str)

            # Atomic rename (best-effort on Windows)
            if os.path.exists(checkpoint_path):
                os.remove(checkpoint_path)
            os.rename(tmp_path, checkpoint_path)

            self._logger.debug(f"Checkpoint saved: {checkpoint_path}")
            return checkpoint_path

        except Exception as e:
            self._logger.error(f"Failed to save checkpoint for '{metadata.session_id}': {e}")
            # Clean up temp file on failure
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise IOError(f"Checkpoint save failed: {e}") from e

    def load_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a session checkpoint from disk.

        Args:
            session_id: Unique session identifier to load.

        Returns:
            Optional[Dict[str, Any]]: The checkpoint data dictionary, or None
                if no checkpoint exists for the given session_id.
        """
        checkpoint_path = self._checkpoint_path(session_id)

        if not os.path.exists(checkpoint_path):
            self._logger.debug(f"No checkpoint found for session '{session_id}'")
            return None

        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._logger.debug(f"Checkpoint loaded: {checkpoint_path}")
            return data
        except (json.JSONDecodeError, IOError) as e:
            self._logger.error(f"Failed to load checkpoint for '{session_id}': {e}")
            return None

    def restore_metadata(self, checkpoint_data: Dict[str, Any]) -> SessionMetadata:
        """Reconstruct a SessionMetadata instance from checkpoint data.

        Args:
            checkpoint_data: Raw checkpoint dictionary as loaded from disk.

        Returns:
            SessionMetadata: Restored metadata with state set to PAUSED
                (since a restored session starts in paused state).
        """
        meta_dict = checkpoint_data.get("metadata", {})

        # Reconstruct goal results
        goal_results = []
        for gr_dict in meta_dict.get("goal_results", []):
            goal_results.append(GoalResult(
                goal_id=gr_dict.get("goal_id", ""),
                goal=gr_dict.get("goal", ""),
                success=gr_dict.get("success", False),
                final_output=gr_dict.get("final_output"),
                steps_taken=gr_dict.get("steps_taken", 0),
                duration_ms=gr_dict.get("duration_ms", 0.0),
                errors=gr_dict.get("errors", []),
                report=gr_dict.get("report"),
                started_at=gr_dict.get("started_at", 0.0),
                completed_at=gr_dict.get("completed_at", 0.0),
            ))

        metadata = SessionMetadata(
            session_id=meta_dict.get("session_id", ""),
            state=SessionState.PAUSED,  # Restored sessions start paused
            created_at=meta_dict.get("created_at", time.time()),
            last_activity_at=meta_dict.get("last_activity_at", time.time()),
            goals_submitted=meta_dict.get("goals_submitted", 0),
            goals_completed=meta_dict.get("goals_completed", 0),
            goals_failed=meta_dict.get("goals_failed", 0),
            total_actions=meta_dict.get("total_actions", 0),
            total_duration_ms=meta_dict.get("total_duration_ms", 0.0),
            goal_results=goal_results,
        )
        return metadata

    def restore_config(self, checkpoint_data: Dict[str, Any]) -> SessionConfig:
        """Reconstruct a SessionConfig instance from checkpoint data.

        Args:
            checkpoint_data: Raw checkpoint dictionary as loaded from disk.

        Returns:
            SessionConfig: Restored configuration.
        """
        cfg_dict = checkpoint_data.get("config", {})
        return SessionConfig(
            max_goals=cfg_dict.get("max_goals", 50),
            goal_timeout_seconds=cfg_dict.get("goal_timeout_seconds", 300.0),
            session_timeout_seconds=cfg_dict.get("session_timeout_seconds", 3600.0),
            max_actions_per_goal=cfg_dict.get("max_actions_per_goal", 25),
            persist_session=cfg_dict.get("persist_session", False),
            persist_directory=cfg_dict.get("persist_directory", ".browser_artifacts/sessions"),
            consolidate_memory_on_goal_complete=cfg_dict.get(
                "consolidate_memory_on_goal_complete", True
            ),
            auto_screenshot_on_goal_complete=cfg_dict.get(
                "auto_screenshot_on_goal_complete", False
            ),
            cleanup_on_close=cfg_dict.get("cleanup_on_close", True),
        )

    def delete_checkpoint(self, session_id: str) -> bool:
        """Delete a session checkpoint file from disk.

        Args:
            session_id: Unique session identifier.

        Returns:
            bool: True if the file was deleted, False if it didn't exist.
        """
        checkpoint_path = self._checkpoint_path(session_id)
        if os.path.exists(checkpoint_path):
            try:
                os.remove(checkpoint_path)
                self._logger.debug(f"Checkpoint deleted: {checkpoint_path}")
                return True
            except OSError as e:
                self._logger.error(f"Failed to delete checkpoint: {e}")
                return False
        return False

    def list_sessions(self) -> list:
        """List all available session checkpoint IDs.

        Returns:
            list: Session IDs that have checkpoint files on disk.
        """
        sessions = []
        try:
            for filename in os.listdir(self.persist_directory):
                if filename.endswith(".checkpoint.json"):
                    session_id = filename.replace(".checkpoint.json", "")
                    sessions.append(session_id)
        except OSError:
            pass
        return sessions
