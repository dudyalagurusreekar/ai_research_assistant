"""Rule Engine for deterministic browser decisions, retries, and wait strategies."""

from typing import Any, Dict, Optional


class BrowserRuleEngine:
    """Evaluates deterministic browser rules (navigation, wait, retry) without LLM intervention."""

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries

    def should_retry(self, action: str, attempts: int, error: Optional[str] = None) -> bool:
        """Determine if a failed action should be retried."""
        if attempts >= self.max_retries:
            return False
        if error and ("TIMEOUT" in error.upper() or "NETWORK" in error.upper() or "DETACHED" in error.upper()):
            return True
        return attempts < 2

    def get_wait_strategy(self, action: str) -> float:
        """Determine recommended wait duration in seconds before or after action."""
        action_lower = action.lower()
        if action_lower in ("navigate", "open_url"):
            return 3.0
        elif action_lower in ("click", "submit"):
            return 1.0
        elif action_lower == "type":
            return 0.5
        return 0.2

    def sanitize_navigation_url(self, raw_url: str) -> str:
        """Enforce valid URL formatting."""
        url = raw_url.strip()
        if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("about:"):
            url = "https://" + url
        return url
