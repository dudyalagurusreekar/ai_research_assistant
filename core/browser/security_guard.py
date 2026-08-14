"""Security Policy Guard for Browser Automation Platform."""

from typing import List, Optional
from urllib.parse import urlparse
from core.browser.models import WorkflowStep

FORBIDDEN_KEYWORDS = ["captcha", "recaptcha", "hcaptcha", "turnstile", "bypass", "crack"]
HIGH_RISK_ACTION_KEYWORDS = ["delete", "pay", "checkout", "transfer", "remove", "destroy", "purchase"]
BLOCKED_SCHEMES = ["file", "gopher", "dict"]


class BrowserSecurityGuard:
    """Enforces security boundaries for automated browser interactions."""

    def __init__(self, allowed_domains: Optional[List[str]] = None, blocked_domains: Optional[List[str]] = None):
        self.allowed_domains = allowed_domains or []
        self.blocked_domains = blocked_domains or ["localhost", "127.0.0.1", "169.254.169.254"]  # Prevent SSRF to internal metadata

    def validate_url(self, url: str) -> bool:
        """Verify target URL complies with security policies."""
        parsed = urlparse(url)
        if parsed.scheme in BLOCKED_SCHEMES:
            raise ValueError(f"Security Policy Error: Blocked URI scheme '{parsed.scheme}'.")

        hostname = parsed.hostname or ""
        if any(hostname == bd or hostname.endswith("." + bd) for bd in self.blocked_domains):
            raise ValueError(f"Security Policy Error: Domain '{hostname}' is restricted from automated access.")

        if self.allowed_domains:
            if not any(hostname == ad or hostname.endswith("." + ad) for ad in self.allowed_domains):
                raise ValueError(f"Security Policy Error: Domain '{hostname}' is not in allowed domain whitelist.")

        return True

    def validate_action(self, step: WorkflowStep) -> WorkflowStep:
        """Inspect workflow action for security risks or CAPTCHA bypass attempts."""
        val_lower = (step.value or "").lower()
        sel_lower = (step.selector or "").lower()

        # Enforce anti-CAPTCHA bypass policy
        if any(kw in val_lower or kw in sel_lower for kw in FORBIDDEN_KEYWORDS):
            raise PermissionError("Security Policy Violation: Bypassing CAPTCHA or anti-bot access controls is strictly forbidden.")

        # Require confirmation for high-impact actions
        if any(kw in val_lower or kw in sel_lower for kw in HIGH_RISK_ACTION_KEYWORDS):
            step.require_confirmation = True

        return step
