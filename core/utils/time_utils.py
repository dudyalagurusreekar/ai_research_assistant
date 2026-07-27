"""Timestamp and datetime utilities."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current datetime in UTC timezone."""
    return datetime.now(timezone.utc)


def utc_isoformat() -> str:
    """Return the current UTC timestamp formatted as ISO-8601 string."""
    return utc_now().isoformat()
