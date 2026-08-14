"""IntegrationCache multi-tier TTL and persistent disk caching layer."""

from typing import Dict, Any, Optional, Set
import time
import json
import os
import re

from infrastructure.logging.logger import StructuredLogger


class IntegrationCache:
    """Multi-tier cache supporting in-memory TTL and persistent file backup."""

    def __init__(self, cache_dir: Optional[str] = None, default_ttl_seconds: int = 300) -> None:
        self._logger = StructuredLogger("IntegrationCache")
        self._cache_dir = cache_dir or ".storage/cache"
        self._default_ttl = default_ttl_seconds
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._tags: Dict[str, Set[str]] = {}

    def _generate_key(self, service: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        param_str = json.dumps(params or {}, sort_keys=True)
        return f"{service.lower()}:{endpoint.lower()}:{param_str}"

    def _sanitize_filename(self, key: str) -> str:
        safe_key = re.sub(r'[^a-zA-Z0-9_-]', '_', key)
        return f"{safe_key[:100]}.json"

    def get(self, service: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Retrieve non-expired cached value."""
        key = self._generate_key(service, endpoint, params)
        now = time.time()

        if key in self._memory_store:
            entry = self._memory_store[key]
            if now < entry["expires_at"]:
                return entry["data"]
            else:
                del self._memory_store[key]

        # Check persistent file backup
        file_path = os.path.join(self._cache_dir, self._sanitize_filename(key))
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                    if now < entry["expires_at"]:
                        self._memory_store[key] = entry
                        return entry["data"]
            except Exception:
                pass

        return None

    def set(
        self,
        service: str,
        endpoint: str,
        data: Any,
        params: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None,
        tags: Optional[Set[str]] = None,
    ) -> None:
        """Store value in memory and disk cache."""
        key = self._generate_key(service, endpoint, params)
        ttl = ttl_seconds or self._default_ttl
        expires_at = time.time() + ttl

        entry = {"data": data, "expires_at": expires_at, "created_at": time.time()}
        self._memory_store[key] = entry

        # Associate tags
        if tags:
            for tag in tags:
                if tag not in self._tags:
                    self._tags[tag] = set()
                self._tags[tag].add(key)

        # Persist to disk
        try:
            os.makedirs(self._cache_dir, exist_ok=True)
            file_path = os.path.join(self._cache_dir, self._sanitize_filename(key))
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(entry, f)
        except Exception as e:
            self._logger.warning(f"Failed to persist cache key '{key}': {e}")

    def invalidate_service(self, service_name: str) -> int:
        """Invalidate all cached items for a given service."""
        prefix = f"{service_name.lower()}:"
        to_delete = [k for k in self._memory_store.keys() if k.startswith(prefix)]
        for k in to_delete:
            del self._memory_store[k]
            file_path = os.path.join(self._cache_dir, self._sanitize_filename(k))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        return len(to_delete)

    def invalidate_tag(self, tag: str) -> int:
        """Invalidate all keys associated with tag."""
        keys = self._tags.get(tag, set())
        count = 0
        for k in keys:
            if k in self._memory_store:
                del self._memory_store[k]
                file_path = os.path.join(self._cache_dir, self._sanitize_filename(k))
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                count += 1
        self._tags[tag] = set()
        return count
