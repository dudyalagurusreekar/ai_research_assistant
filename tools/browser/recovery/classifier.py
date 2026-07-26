"""Error Taxonomy and Classification System.

Analyzes error messages and exception signatures to map failures into
well-defined ErrorCategory groups.
"""

import re
from enum import Enum
from typing import List, Optional, Tuple

logger = re.compile  # Dummy reference to keep imports simple


class ErrorCategory(str, Enum):
    """Classification of browser execution failure types."""

    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    ELEMENT_NOT_INTERACTABLE = "ELEMENT_NOT_INTERACTABLE"
    STALE_ELEMENT = "STALE_ELEMENT"
    NAVIGATION_FAILURE = "NAVIGATION_FAILURE"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    DIALOG_BLOCKING = "DIALOG_BLOCKING"
    JS_EXCEPTION = "JS_EXCEPTION"
    AUTH_INTERRUPTION = "AUTH_INTERRUPTION"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    BROWSER_CRASH = "BROWSER_CRASH"
    CAPTCHA_INTERRUPTION = "CAPTCHA_INTERRUPTION"
    UNKNOWN = "UNKNOWN"


# Regex-based rules mapped to ErrorCategory. Sorted by match specificity.
_CLASSIFICATION_RULES: List[Tuple[re.Pattern, ErrorCategory]] = [
    (re.compile(r"stale|detached|removed from dom|staleelementreference", re.I), ErrorCategory.STALE_ELEMENT),
    (re.compile(r"not found|no element|elementnotfounderror|unable to locate|cannot find element", re.I), ErrorCategory.ELEMENT_NOT_FOUND),
    (re.compile(r"not clickable|intercepted|obscured|overlay|not interactable|is not clickable", re.I), ErrorCategory.ELEMENT_NOT_INTERACTABLE),
    (re.compile(r"dialog|alert|DialogError|modal", re.I), ErrorCategory.DIALOG_BLOCKING),
    (re.compile(r"session.*expired|SessionError|session.*invalid", re.I), ErrorCategory.SESSION_EXPIRED),
    (re.compile(r"login|sign.?in|unauthorized|401|403|auth", re.I), ErrorCategory.AUTH_INTERRUPTION),
    (re.compile(r"net::|connection refused|NetworkError|dns|disconnected|offline", re.I), ErrorCategory.NETWORK_ERROR),
    (re.compile(r"crash|target closed|context destroyed|unresponsive|browser disconnected|page crashed", re.I), ErrorCategory.BROWSER_CRASH),
    (re.compile(r"captcha|recaptcha|hcaptcha|cloudflare|verify you are human", re.I), ErrorCategory.CAPTCHA_INTERRUPTION),
    (re.compile(r"timeout|timed?\s*out|navigation timeout", re.I), ErrorCategory.TIMEOUT),
    (re.compile(r"navigation|ERR_|NavigationError", re.I), ErrorCategory.NAVIGATION_FAILURE),
    (re.compile(r"javascript|script|ScriptExecutionError|js error", re.I), ErrorCategory.JS_EXCEPTION),
]


class ErrorClassifier:
    """Classifies raw failure logs into categorized ErrorCategory taxonomy enums."""

    @staticmethod
    def classify(error_message: str, exception: Optional[Exception] = None) -> ErrorCategory:
        """Classify an error message string and exception signature.

        Args:
            error_message: Error text.
            exception: Optional Exception class instance.

        Returns:
            ErrorCategory: The classified failure category.
        """
        combined_text = error_message or ""
        if exception:
            combined_text += f" {type(exception).__name__} {str(exception)}"

        for pattern, category in _CLASSIFICATION_RULES:
            if pattern.search(combined_text):
                return category

        return ErrorCategory.UNKNOWN
