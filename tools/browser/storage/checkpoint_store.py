"""Disk-backed asynchronous and synchronous Checkpoint Store."""

import os
import json
import logging
from typing import Any, Callable, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, Future

logger = logging.getLogger("BrowserStorage.CheckpointStore")


class DiskCheckpointStore:
    """Handles saving and restoring planner and context checkpoints on a separate IO thread."""

    def __init__(self) -> None:
        """Initialize DiskCheckpointStore."""
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="CheckpointStoreWorker")
        self._logger = logger

    def save_checkpoint_sync(self, state_dict: Dict[str, Any], filepath: str) -> None:
        """Save a state checkpoint dictionary to disk synchronously.

        Args:
            state_dict (Dict[str, Any]): Serialized state dictionary.
            filepath (str): Target local file path.
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(state_dict, f, indent=2)
            self._logger.info(f"Saved state checkpoint to '{filepath}'")
        except Exception as e:
            self._logger.error(f"Failed to save state checkpoint to '{filepath}': {e}")
            raise e

    def save_checkpoint_async(
        self,
        state_dict: Dict[str, Any],
        filepath: str,
        callback: Optional[Callable[[str], None]] = None,
    ) -> Future:
        """Save a state checkpoint dictionary to disk asynchronously.

        Args:
            state_dict (Dict[str, Any]): Serialized state dictionary.
            filepath (str): Target local file path.
            callback (Optional[Callable[[str], None]]): Callback triggered with filepath upon success.

        Returns:
            Future: Thread execution future wrapper.
        """
        def _task():
            self.save_checkpoint_sync(state_dict, filepath)
            if callback:
                try:
                    callback(filepath)
                except Exception as cb_err:
                    self._logger.error(f"Callback failed in async checkpoint write: {cb_err}")
            return filepath

        return self._executor.submit(_task)

    def load_checkpoint(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Load and return a checkpoint dictionary from disk.

        Args:
            filepath (str): Source local file path.

        Returns:
            Optional[Dict[str, Any]]: The parsed checkpoint state dictionary or None if not found/invalid.
        """
        if not os.path.exists(filepath):
            self._logger.info(f"No checkpoint file found at '{filepath}'")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._logger.info(f"Loaded checkpoint dictionary from '{filepath}'")
            return data
        except Exception as e:
            self._logger.error(f"Failed to parse checkpoint file at '{filepath}': {e}")
            return None

    def shutdown(self) -> None:
        """Shutdown the underlying thread executor."""
        self._executor.shutdown(wait=True)


# Default Singleton Instantiation
CheckpointStore = DiskCheckpointStore()
