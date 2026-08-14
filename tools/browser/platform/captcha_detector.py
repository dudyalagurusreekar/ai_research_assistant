"""CAPTCHA Detection Engine for Sprint 11 Browser Automation Platform."""

import logging
import re
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup
from tools.browser.platform.models import CaptchaDetectionResult

logger = logging.getLogger("Tools.Browser.Platform.CaptchaDetector")


class CaptchaDetector:
    """Identifies bot challenges, reCAPTCHAs, hCaptchas, and Turnstiles. Strictly halts execution without attempting bypass."""

    CAPTCHA_SIGNATURES = {
        "recaptcha": [
            r"google\.com/recaptcha",
            r"g-recaptcha",
            r"recaptcha-token",
            r"grecaptcha",
        ],
        "hcaptcha": [
            r"hcaptcha\.com",
            r"h-captcha",
            r"hcaptcha-response",
        ],
        "turnstile": [
            r"challenges\.cloudflare\.com",
            r"cf-turnstile",
            r"turnstile-wrapper",
        ],
        "geetest": [
            r"gt_captcha",
            r"geetest\.com",
            r"geetest_holder",
        ],
        "bot_block": [
            r"access denied",
            r"captcha",
            r"please verify you are a human",
            r"bot detection",
            r"pardon our interruption",
            r"security check",
        ],
    }

    async def detect_captcha(self, page: Any) -> CaptchaDetectionResult:
        """Scan active page DOM and network state for CAPTCHA / bot challenge presence."""
        html_content = ""
        url = getattr(page, "url", "")

        if hasattr(page, "content"):
            try:
                html_content = await page.content()
            except Exception as e:
                logger.warning(f"Error reading page content for CAPTCHA scan: {e}")

        if not html_content:
            return CaptchaDetectionResult(captcha_detected=False)

        soup = BeautifulSoup(html_content, "html.parser")
        text_lower = soup.get_text(separator=" ", strip=True).lower()
        html_lower = html_content.lower()

        for provider, patterns in self.CAPTCHA_SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, html_lower, re.IGNORECASE):
                    # Check text context if bot_block
                    if provider == "bot_block":
                        if not any(phrase in text_lower for phrase in ["verify you are human", "pardon our interruption", "captcha", "security check"]):
                            continue

                    logger.warning(f"CAPTCHA / Bot Challenge detected! Provider: '{provider}', Pattern: '{pattern}' on '{url}'.")
                    return CaptchaDetectionResult(
                        captcha_detected=True,
                        provider=provider,
                        confidence=0.95,
                        details=f"Detected '{provider}' challenge matching pattern '{pattern}'. Automated bypass is prohibited.",
                    )

        return CaptchaDetectionResult(captcha_detected=False, confidence=0.0)
