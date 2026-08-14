"""Authentication Manager for Sprint 11 Browser Automation Platform."""

import logging
import time
from typing import Any, Dict, Optional
from tools.browser.platform.models import ActionResult, ActionType

logger = logging.getLogger("Tools.Browser.Platform.AuthManager")


class AuthenticationManager:
    """Handles automated login form submission, HTTP Basic auth, bearer tokens, and session reuse."""

    def __init__(self) -> None:
        self._credentials_vault: Dict[str, Dict[str, str]] = {}

    def register_credentials(self, domain: str, username: str, password: str) -> None:
        """Store credentials for domain in volatile memory vault."""
        self._credentials_vault[domain] = {
            "username": username,
            "password": password,
        }
        logger.info(f"Registered credentials for domain '{domain}'.")

    async def perform_form_login(
        self,
        page: Any,
        url: str,
        username: str,
        password: str,
        username_selector: str = "input[type='text'], input[type='email'], input[name='username']",
        password_selector: str = "input[type='password']",
        submit_selector: str = "button[type='submit'], input[type='submit']",
        timeout_ms: int = 15000,
    ) -> ActionResult:
        """Perform automated form login."""
        start_time = time.time()
        try:
            if hasattr(page, "goto"):
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            if hasattr(page, "fill"):
                await page.fill(username_selector, username, timeout=timeout_ms)
                await page.fill(password_selector, password, timeout=timeout_ms)

            if hasattr(page, "click"):
                await page.click(submit_selector, timeout=timeout_ms)

            current_url = getattr(page, "url", url)
            exec_time = (time.time() - start_time) * 1000
            return ActionResult(
                success=True,
                action_type=ActionType.TYPE,
                message=f"Form login submitted for '{username}' at '{current_url}'.",
                url=current_url,
                execution_time_ms=exec_time,
                data={"username": username, "domain": url},
            )
        except Exception as e:
            exec_time = (time.time() - start_time) * 1000
            logger.error(f"Form login failed for '{url}': {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE,
                message=f"Form login failed for '{url}': {e}",
                url=url,
                error=str(e),
                execution_time_ms=exec_time,
            )

    async def inject_bearer_token(self, context: Any, token: str) -> bool:
        """Inject Bearer token authorization header into context."""
        if hasattr(context, "set_extra_http_headers"):
            try:
                await context.set_extra_http_headers({"Authorization": f"Bearer {token}"})
                logger.info("Successfully injected Authorization Bearer token into context headers.")
                return True
            except Exception as e:
                logger.error(f"Failed to inject bearer token: {e}")
                return False
        return False
