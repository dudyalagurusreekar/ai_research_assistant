"""Strict JSON serialization boundary for Browser Tool API.

Ensures that no Playwright objects, lambdas, or complex Python objects
leak across the API boundary into the agent context.
"""

import json
from typing import Any


def sanitize_payload(obj: Any, depth: int = 0, max_depth: int = 5) -> Any:
    """Recursively sanitize a Python object to ensure it is JSON serializable.

    Strips out complex objects, functions, and Playwright handles, replacing
    them with descriptive string placeholders.

    Args:
        obj: Any Python object.
        depth: Current recursion depth.
        max_depth: Maximum allowed recursion depth before truncating.

    Returns:
        A strictly JSON-serializable structure (dict, list, str, int, float, bool, None).
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool, bytes)):
        return obj

    if depth >= max_depth:
        return "<Max Depth Exceeded>"

    if isinstance(obj, dict):
        sanitized_dict = {}
        for k, v in obj.items():
            # Keys must be strings in JSON
            key_str = str(k) if not isinstance(k, str) else k
            sanitized_dict[key_str] = sanitize_payload(v, depth + 1, max_depth)
        return sanitized_dict

    if isinstance(obj, (list, tuple, set)):
        return [sanitize_payload(item, depth + 1, max_depth) for item in obj]

    # Try to extract useful information if it has a __dict__ or to_dict
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        try:
            return sanitize_payload(obj.to_dict(), depth + 1, max_depth)
        except Exception:
            pass
            
    if hasattr(obj, "__dict__"):
        try:
            return sanitize_payload(obj.__dict__, depth + 1, max_depth)
        except Exception:
            pass

    # Handle specific complex objects common in browser automation
    obj_type_name = type(obj).__name__
    
    # Playwright ElementHandle, JSHandle, Page, Context -> Drop them to prevent leakage
    if "ElementHandle" in obj_type_name or "JSHandle" in obj_type_name or "Page" in obj_type_name or "BrowserContext" in obj_type_name:
        return None
        
    # Functions and Callables -> Drop them
    if callable(obj):
        return None

    # Fallback to None for strict primitive adherence instead of weird strings
    return None


class BrowserJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Browser Tool payloads that safely encodes bytes to base64."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, bytes):
            import base64
            try:
                return base64.b64encode(obj).decode("utf-8")
            except Exception:
                return "<Binary Data>"
        return super().default(obj)


def to_json_str(obj: Any, indent: int = 2) -> str:
    """Serialize a Python structure to JSON string, encoding binary data safely."""
    return json.dumps(obj, indent=indent, cls=BrowserJSONEncoder)

