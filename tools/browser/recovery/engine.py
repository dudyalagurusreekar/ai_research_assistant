"""Browser Recovery Engine for checkpointing and restoring state after crashes."""

import logging
from typing import Dict, Optional
from infrastructure.storage.storage import IStorage, DiskStorage
from tools.browser.state.models import BrowserStateModel

logger = logging.getLogger("Tools.Browser.Recovery")


class BrowserRecoveryEngine:
    """Saves and restores browser state snapshots to/from persistent storage for crash recovery."""

    def __init__(self, storage: Optional[IStorage] = None) -> None:
        self.storage = storage or DiskStorage(base_dir=".browser_checkpoints")
        self._logger = logger

    async def save_snapshot(self, session_id: str, state: BrowserStateModel) -> bool:
        """Save a browser state snapshot to persistent storage."""
        checkpoint_id = f"browser_state_{session_id}"
        success = await self.storage.save_checkpoint(checkpoint_id, state.to_dict())
        if success:
            self._logger.info(f"Saved browser state checkpoint '{checkpoint_id}'.")
        return success

    async def restore_snapshot(self, session_id: str) -> Optional[BrowserStateModel]:
        """Restore browser state snapshot from storage."""
        checkpoint_id = f"browser_state_{session_id}"
        snapshot = await self.storage.load_checkpoint(checkpoint_id)
        if not snapshot:
            self._logger.warning(f"No checkpoint found for session '{session_id}'.")
            return None

        restored_state = BrowserStateModel(
            url=snapshot.get("url", "about:blank"),
            active_tab_id=snapshot.get("active_tab_id", "tab_1"),
            history=snapshot.get("history", []),
            uploads=snapshot.get("uploads", []),
            dom_version_hash=snapshot.get("dom_version_hash", ""),
        )
        self._logger.info(f"Restored browser state for session '{session_id}' at URL '{restored_state.url}'.")
        return restored_state
