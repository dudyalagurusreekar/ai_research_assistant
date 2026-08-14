"""Playwright Browser Instance & Context Lifecycle Manager."""

import asyncio
import logging
import uuid
from typing import Dict, Optional, Any
from core.browser.models import BrowserSessionConfig, PageMetadata
from core.browser.security_guard import BrowserSecurityGuard

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]


class BrowserManager:
    """Manages Playwright browser instances, context pools, and session states."""

    def __init__(self, security_guard: Optional[BrowserSecurityGuard] = None):
        self.security_guard = security_guard or BrowserSecurityGuard()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._playwright_instance = None

    async def initialize(self):
        """Initialize Playwright automation engine if available."""
        try:
            from playwright.async_api import async_playwright
            self._playwright_instance = await async_playwright().start()
            logger.info("Playwright automation engine initialized successfully.")
        except Exception as e:
            logger.warning(f"Playwright async API not available ({e}). Running in simulation mode.")

    async def create_session(self, config: BrowserSessionConfig) -> Dict[str, Any]:
        """Create and register a new browser session context."""
        session_id = config.session_id or f"bs_{uuid.uuid4().hex[:8]}"
        user_agent = config.user_agent or USER_AGENTS[0]

        session_entry = {
            "config": config,
            "session_id": session_id,
            "browser": None,
            "context": None,
            "page": None,
            "current_url": "about:blank",
            "is_active": True,
            "history": [],
        }

        if self._playwright_instance:
            try:
                browser_type = getattr(self._playwright_instance, config.browser_type, self._playwright_instance.chromium)
                browser = await browser_type.launch(
                    headless=config.headless,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
                )
                context = await browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": config.viewport_width, "height": config.viewport_height},
                    ignore_https_errors=True,
                )
                page = await context.new_page()

                session_entry["browser"] = browser
                session_entry["context"] = context
                session_entry["page"] = page
            except Exception as ex:
                logger.warning(f"Failed to launch live Playwright browser: {ex}. Falling back to simulation mode.")

        self.active_sessions[session_id] = session_entry
        logger.info(f"Created browser session '{session_id}' (browser: {config.browser_type}).")
        return session_entry

    async def close_session(self, session_id: str):
        """Close browser context and release resources."""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        session["is_active"] = False
        if session.get("browser"):
            try:
                await session["browser"].close()
            except Exception as e:
                logger.error(f"Error closing browser for session '{session_id}': {e}")

        del self.active_sessions[session_id]
        logger.info(f"Closed browser session '{session_id}'.")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve active session state dict."""
        return self.active_sessions.get(session_id)
