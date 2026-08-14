"""Session Manager for Sprint 11 Browser Automation Platform."""

import os
import json
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from tools.browser.platform.models import SessionConfig

logger = logging.getLogger("Tools.Browser.Platform.SessionManager")


class SessionManager:
    """Manages browser session states, cookie persistence, storage exports, and profile isolation."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self.storage_dir = Path(storage_dir or ".storage/sessions")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._active_sessions: Dict[str, SessionConfig] = {}

    def create_session(
        self,
        session_id: str,
        cookies: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> SessionConfig:
        """Create a new session configuration profile."""
        config = SessionConfig(
            session_id=session_id,
            cookies=cookies or [],
            headers=headers or {},
            created_at=time.time(),
            updated_at=time.time(),
        )
        self._active_sessions[session_id] = config
        logger.info(f"Created session configuration for '{session_id}'.")
        return config

    def get_session(self, session_id: str) -> Optional[SessionConfig]:
        """Retrieve active session config."""
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
        return self.load_session(session_id)

    async def save_session(self, session_id: str, context: Optional[Any] = None) -> bool:
        """Save session state to file storage."""
        config = self._active_sessions.get(session_id) or SessionConfig(session_id=session_id)

        if context and hasattr(context, "cookies"):
            try:
                cookies = await context.cookies()
                config.cookies = cookies
            except Exception as e:
                logger.warning(f"Could not extract cookies from context for '{session_id}': {e}")

        config.updated_at = time.time()
        file_path = self.storage_dir / f"{session_id}.json"

        data = {
            "session_id": config.session_id,
            "cookies": config.cookies,
            "local_storage": config.local_storage,
            "session_storage": config.session_storage,
            "headers": config.headers,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._active_sessions[session_id] = config
            logger.info(f"Successfully saved session '{session_id}' to '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to save session state for '{session_id}': {e}")
            return False

    def load_session(self, session_id: str) -> Optional[SessionConfig]:
        """Load session state from file storage."""
        file_path = self.storage_dir / f"{session_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            config = SessionConfig(
                session_id=data["session_id"],
                cookies=data.get("cookies", []),
                local_storage=data.get("local_storage", {}),
                session_storage=data.get("session_storage", {}),
                headers=data.get("headers", {}),
                created_at=data.get("created_at", time.time()),
                updated_at=data.get("updated_at", time.time()),
            )
            self._active_sessions[session_id] = config
            logger.info(f"Loaded session '{session_id}' from storage.")
            return config
        except Exception as e:
            logger.error(f"Failed to load session state for '{session_id}': {e}")
            return None

    async def restore_session_to_context(self, session_id: str, context: Any) -> bool:
        """Apply session cookies and storage to Playwright context."""
        session = self.get_session(session_id)
        if not session or not context:
            return False

        if session.cookies and hasattr(context, "add_cookies"):
            try:
                await context.add_cookies(session.cookies)
                logger.info(f"Applied {len(session.cookies)} cookies to context for '{session_id}'.")
            except Exception as e:
                logger.warning(f"Error applying cookies to context for '{session_id}': {e}")

        if session.headers and hasattr(context, "set_extra_http_headers"):
            try:
                await context.set_extra_http_headers(session.headers)
            except Exception as e:
                logger.warning(f"Error applying extra headers for '{session_id}': {e}")

        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete session profile and storage file."""
        self._active_sessions.pop(session_id, None)
        file_path = self.storage_dir / f"{session_id}.json"
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted session storage for '{session_id}'.")
                return True
            except Exception as e:
                logger.error(f"Failed to delete session file '{file_path}': {e}")
                return False
        return True
