"""ID Generator utilities for generating unique identifiers."""

import uuid


def generate_id(prefix: str = "") -> str:
    """Generate a unique UUIDv4 string, optionally prefixed.

    Args:
        prefix: Optional prefix string (e.g. 'sess_', 'req_', 'evt_').

    Returns:
        String identifier.
    """
    unique_str = str(uuid.uuid4())
    if prefix:
        return f"{prefix}{unique_str}"
    return unique_str
