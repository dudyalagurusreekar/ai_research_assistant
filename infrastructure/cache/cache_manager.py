"""High-level CacheManager providing specialized keyspaces for Sessions, Rate Limiting, Planner, and Workflows."""

import json
import time
from typing import Any, Dict, List, Optional
from infrastructure.cache.redis_client import redis_manager
from utils.logger import get_logger

logger = get_logger("CacheManager")


class CacheManager:
    """Unified cache interface providing namespaced keyspace operations."""

    def __init__(self, client_manager=None):
        self._manager = client_manager or redis_manager

    @property
    def client(self):
        return self._manager.get_client()

    # --- 1. General Key-Value Caching ---
    def get(self, key: str) -> Optional[Any]:
        """Fetch and deserialize JSON value by key."""
        try:
            raw = self.client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            return self.client.get(key)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = 3600) -> bool:
        """Serialize and set key with optional TTL."""
        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            return bool(self.client.set(key, serialized, ex=ttl_seconds))
        except Exception as exc:
            logger.error(f"Cache set failed for key '{key}': {exc}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        return bool(self.client.delete(key))

    def clear_namespace(self, prefix: str) -> int:
        """Clear all keys matching prefix."""
        keys = self.client.keys(f"{prefix}*")
        if keys:
            return self.client.delete(*keys)
        return 0

    # --- 2. Session Management Keyspace ---
    def store_session(self, session_token: str, user_data: Dict[str, Any], ttl_seconds: int = 86400) -> bool:
        """Store active user web session."""
        key = f"session:{session_token}"
        return self.set(key, user_data, ttl_seconds=ttl_seconds)

    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Retrieve active user web session."""
        key = f"session:{session_token}"
        return self.get(key)

    def revoke_session(self, session_token: str) -> bool:
        """Revoke active user web session."""
        key = f"session:{session_token}"
        return self.delete(key)

    # --- 3. Sliding Window Rate Limiting ---
    def check_rate_limit(self, identifier: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """Check if action is allowed under rate limit window. Returns True if allowed, False if exceeded."""
        key = f"ratelimit:{identifier}"
        now = time.time()
        window_start = now - window_seconds
        
        try:
            # Simple timestamp list check for fallback / basic redis
            raw = self.get(key)
            timestamps: List[float] = raw if isinstance(raw, list) else []
            # Filter timestamps within window
            timestamps = [ts for ts in timestamps if ts > window_start]
            
            if len(timestamps) >= max_requests:
                return False
            
            timestamps.append(now)
            self.set(key, timestamps, ttl_seconds=window_seconds)
            return True
        except Exception as exc:
            logger.error(f"Rate limit check error for {identifier}: {exc}")
            return True

    # --- 4. Planner Caches ---
    def cache_planner_dag(self, plan_id: str, dag_payload: Dict[str, Any], ttl_seconds: int = 7200) -> bool:
        """Cache an execution plan DAG."""
        key = f"planner:dag:{plan_id}"
        return self.set(key, dag_payload, ttl_seconds=ttl_seconds)

    def get_planner_dag(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Fetch cached execution plan DAG."""
        key = f"planner:dag:{plan_id}"
        return self.get(key)

    # --- 5. Browser Automation State ---
    def store_browser_state(self, session_id: str, state_data: Dict[str, Any], ttl_seconds: int = 1800) -> bool:
        """Store transient browser DOM / cookie checkpoint state."""
        key = f"browser:state:{session_id}"
        return self.set(key, state_data, ttl_seconds=ttl_seconds)

    def get_browser_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve browser automation checkpoint state."""
        key = f"browser:state:{session_id}"
        return self.get(key)

    # --- 6. Background Workflow State ---
    def set_workflow_state(self, execution_id: str, state: Dict[str, Any], ttl_seconds: int = 86400) -> bool:
        """Store real-time background workflow status."""
        key = f"workflow:state:{execution_id}"
        return self.set(key, state, ttl_seconds=ttl_seconds)

    def get_workflow_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve real-time background workflow status."""
        key = f"workflow:state:{execution_id}"
        return self.get(key)


# Global CacheManager instance
cache_manager = CacheManager()
