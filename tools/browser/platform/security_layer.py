"""Security Layer for Sprint 11 Browser Automation Platform."""

import logging
import re
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse
from tools.browser.platform.models import BrowserAction, SecurityAssessmentResult

logger = logging.getLogger("Tools.Browser.Platform.SecurityLayer")


class SecurityLayer:
    """Enforces safety guardrails, high-impact action gates, user confirmation rules, and domain filtering."""

    HIGH_IMPACT_KEYWORDS = [
        "delete",
        "remove",
        "destroy",
        "purchase",
        "checkout",
        "buy",
        "pay",
        "payment",
        "confirm order",
        "transfer",
        "change password",
        "reset password",
        "clear data",
        "wipe",
        "terminate",
        "cancel subscription",
    ]

    DANGEROUS_PROTOCOLS = {"gopher", "ftp", "telnet", "ssh"}

    def __init__(
        self,
        domain_whitelist: Optional[List[str]] = None,
        domain_blacklist: Optional[List[str]] = None,
        user_confirmation_callback: Optional[Callable[[BrowserAction, SecurityAssessmentResult], bool]] = None,
    ) -> None:
        self.domain_whitelist = domain_whitelist
        self.domain_blacklist = domain_blacklist or []
        self.user_confirmation_callback = user_confirmation_callback

    def assess_action_safety(self, action: BrowserAction, target_url: str = "") -> SecurityAssessmentResult:
        """Evaluate security risk and check if explicit user confirmation is required."""
        reasons = []
        is_high_impact = False
        is_safe = True

        # Check URL protocol & domain rules
        url_to_check = action.url or target_url
        if url_to_check:
            parsed = urlparse(url_to_check)
            scheme = parsed.scheme.lower()
            domain = parsed.netloc.lower()

            if scheme in self.DANGEROUS_PROTOCOLS:
                is_safe = False
                reasons.append(f"Blocked dangerous protocol scheme '{scheme}'.")

            if scheme == "file" and not url_to_check.startswith("file:///"):
                is_safe = False
                reasons.append("Blocked invalid local file URI format.")

            if self.domain_blacklist:
                for b_domain in self.domain_blacklist:
                    if b_domain.lower() in domain:
                        is_safe = False
                        reasons.append(f"Target domain '{domain}' is present on domain blacklist.")

            if self.domain_whitelist:
                whitelisted = any(w_domain.lower() in domain for w_domain in self.domain_whitelist)
                if not whitelisted and domain:
                    is_safe = False
                    reasons.append(f"Target domain '{domain}' is not on domain whitelist.")

        # Check for High-Impact text/selectors
        text_content = f"{action.text or ''} {action.value or ''} {action.target_selector or ''}".lower()
        for kw in self.HIGH_IMPACT_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_content):
                is_high_impact = True
                reasons.append(f"Action contains high-impact/destructive keyword '{kw}'.")

        risk_level = "low"
        if not is_safe:
            risk_level = "critical"
        elif is_high_impact:
            risk_level = "high"

        requires_confirmation = is_high_impact or not is_safe

        return SecurityAssessmentResult(
            is_safe=is_safe,
            is_high_impact=is_high_impact,
            requires_user_confirmation=requires_confirmation,
            risk_level=risk_level,
            reasons=reasons,
        )

    def request_user_confirmation(self, action: BrowserAction, assessment: SecurityAssessmentResult) -> bool:
        """Prompt or trigger callback for explicit user confirmation on high-impact actions."""
        if not assessment.requires_user_confirmation:
            return True

        if self.user_confirmation_callback:
            approved = self.user_confirmation_callback(action, assessment)
            logger.info(f"User confirmation callback returned '{approved}' for action '{action.action_type.value}'.")
            return approved

        # Default safety policy: Reject high-impact/dangerous actions if no explicit user confirmation callback provided
        logger.warning(
            f"Blocked high-impact action '{action.action_type.value}' because no user confirmation callback was configured. "
            f"Reasons: {assessment.reasons}"
        )
        return False
