"""Persistent request caching system for LLM responses."""

import os
import json
import hashlib
import logging
from typing import Dict, Any, Union, List

logger = logging.getLogger("LLMResilience.Cache")


def serialize_message(m: Any) -> Dict[str, Any]:
    """Helper to convert dictionary or ChatMessage-like objects into standard dictionaries."""
    if isinstance(m, dict):
        return m
    res = {}
    for attr in ("role", "content", "tool_calls"):
        if hasattr(m, attr):
            val = getattr(m, attr)
            if attr == "tool_calls" and val:
                # Convert list of tool calls to string signatures
                res[attr] = [str(tc) for tc in val]
            else:
                res[attr] = val
    return res


class RequestCache:
    """File-based persistent request cache for LLM completion requests."""

    def __init__(self, cache_file: str = "logs/llm_cache.json") -> None:
        self.cache_file = cache_file
        self.cache: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Loads cache items from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    self.cache = json.load(f)
                logger.debug(f"Loaded {len(self.cache)} entries from request cache.")
            except Exception as e:
                logger.warning(f"Failed to read LLM request cache file: {e}")
                self.cache = {}

    def save(self) -> None:
        """Saves current cache to disk."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save LLM request cache file: {e}")

    def _get_key(self, messages: List[Any], kwargs: Dict[str, Any]) -> str:
        """Generates a stable SHA-256 hash representing the request content and configuration."""
        serialized_messages = [serialize_message(m) for m in messages]
        
        # Capture critical parameters that influence response content
        stable_data = {
            "messages": serialized_messages,
            "model": kwargs.get("model"),
            "temperature": kwargs.get("temperature", 0.0),
            "max_tokens": kwargs.get("max_tokens"),
            "response_format": kwargs.get("response_format"),
            "stop": kwargs.get("stop"),
        }
        
        serialized_str = json.dumps(stable_data, sort_keys=True)
        return hashlib.sha256(serialized_str.encode("utf-8")).hexdigest()

    def get(self, messages: List[Any], kwargs: Dict[str, Any]) -> Union[Dict[str, Any], None]:
        """Retrieves a cached response if present, otherwise returns None."""
        key = self._get_key(messages, kwargs)
        cached_response = self.cache.get(key)
        if cached_response:
            logger.info("Request Cache hit. Reusing cached response.")
            return cached_response
        return None

    def set(self, messages: List[Any], kwargs: Dict[str, Any], response: Any) -> None:
        """Saves a raw completion response payload to the cache."""
        key = self._get_key(messages, kwargs)
        
        # If response is a dict-like/object, serialize it to dict
        response_dict = response
        if hasattr(response, "model_dump"):
            response_dict = response.model_dump()
        elif hasattr(response, "to_dict"):
            response_dict = response.to_dict()

        self.cache[key] = response_dict
        self.save()
