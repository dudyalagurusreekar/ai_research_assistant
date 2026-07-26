"""Disk-backed asynchronous and synchronous Artifact Store."""

import os
import json
import time
import uuid
import logging
from typing import Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, Future

logger = logging.getLogger("BrowserStorage.ArtifactStore")


class DiskArtifactStore:
    """Handles offloading large data payloads and saving screenshots to disk asynchronously."""

    def __init__(self, artifact_dir: str = ".browser_artifacts") -> None:
        """Initialize DiskArtifactStore.

        Args:
            artifact_dir (str): Directory where JSON/text artifacts are saved.
        """
        self.artifact_dir = os.path.abspath(artifact_dir)
        os.makedirs(self.artifact_dir, exist_ok=True)
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ArtifactStoreWorker")
        self._logger = logger

    def save_artifact_sync(self, name: str, data: Any) -> str:
        """Save a data payload to disk synchronously and return its filepath.

        Args:
            name (str): Identifier name prefix.
            data (Any): JSON-serializable data.

        Returns:
            str: Resolved local absolute filepath.
        """
        filename = f"{name}_{int(time.time())}_{uuid.uuid4().hex[:6]}.json"
        filepath = os.path.join(self.artifact_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._logger.info(f"Saved artifact synchronously to '{filepath}'")
            return filepath
        except Exception as e:
            self._logger.error(f"Failed to save artifact '{filename}': {e}")
            raise e

    def save_artifact_async(
        self,
        name: str,
        data: Any,
        callback: Optional[Callable[[str], None]] = None,
    ) -> Future:
        """Save a data payload to disk asynchronously on a background thread.

        Args:
            name (str): Identifier name prefix.
            data (Any): JSON-serializable data.
            callback (Optional[Callable[[str], None]]): Callback triggered with the file path upon success.

        Returns:
            Future: Thread execution future wrapper.
        """
        def _task():
            filepath = self.save_artifact_sync(name, data)
            if callback:
                try:
                    callback(filepath)
                except Exception as cb_err:
                    self._logger.error(f"Callback failed in async artifact write: {cb_err}")
            return filepath

        return self._executor.submit(_task)

    def shutdown(self) -> None:
        """Shutdown the underlying thread executor."""
        self._executor.shutdown(wait=True)


# Default Singleton Instantiation
ArtifactStore = DiskArtifactStore()
