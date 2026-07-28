"""Utility helper placeholders for the Browser Tool.

This module provides standard library helper functions for URL validation,
domain parsing, text cleaning, and unique request ID generation.
"""

import re
import uuid
from urllib.parse import urlparse, urlunparse

from tools.browser.exceptions import ValidationError


def generate_request_id(prefix: str = "req") -> str:
    """Generate a unique request tracking ID.

    Args:
        prefix (str): Prefix string for the UUID.

    Returns:
        str: Unique identifier (e.g. 'req-9b1deb4d3b7d467d').
    """
    unique_suffix = uuid.uuid4().hex[:16]
    return f"{prefix}-{unique_suffix}"


def validate_url(url: str) -> bool:
    """Validate if a string is a properly formatted HTTP/HTTPS URL.

    Args:
        url (str): Target URL string.

    Returns:
        bool: True if valid HTTP/HTTPS URL.

    Raises:
        ValidationError: If URL format is invalid.
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string.")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(
            f"Invalid URL scheme '{parsed.scheme}'. Only 'http' and 'https' are supported."
        )
    if not parsed.netloc:
        raise ValidationError(f"Invalid URL '{url}': Missing domain hostname.")

    return True


def sanitize_url(url: str) -> str:
    """Sanitize and normalize a URL string (stripping fragments and whitespace).

    Args:
        url (str): Raw URL string.

    Returns:
        str: Cleaned normalized URL string.
    """
    url_str = url.strip()
    parsed = urlparse(url_str)
    # Strip URL fragments (#anchor) for web requests
    cleaned_parsed = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path,
        parsed.params,
        parsed.query,
        "",  # Strip fragment
    ))
    return cleaned_parsed


def extract_domain(url: str) -> str:
    """Extract domain host name from a URL.

    Args:
        url (str): Target URL string.

    Returns:
        str: Domain hostname (e.g. 'example.com').
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.split(":")[0]  # Remove port if present
    except Exception:
        return ""


def clean_text(raw_text: str) -> str:
    """Clean and normalize whitespace in extracted text strings.

    Args:
        raw_text (str): Raw text containing redundant whitespace or newlines.

    Returns:
        str: Cleaned text with normalized spacing.
    """
    if not raw_text:
        return ""
    # Collapse multiple whitespace characters into single space
    cleaned = re.sub(r"\s+", " ", raw_text)
    return cleaned.strip()
