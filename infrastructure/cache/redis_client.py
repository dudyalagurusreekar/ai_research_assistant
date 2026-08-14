"""Redis Client Manager with fallback in-memory cache for test isolation."""

import json
import time
from typing import Any, Dict, List, Optional
from infrastructure.cache.redis_config import redis_config
from utils.logger import get_logger

logger = get_logger("RedisClientManager")

try:
    import redis
    HAS_REDIS = True
except ImportError:
    redis = None
    HAS_REDIS = False


class InMemoryCacheFallback:
    """Mock Redis client using Python dictionary for offline/unit test execution."""

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._ttl: Dict[str, float] = {}

    def get(self, key: str) -> Optional[str]:
        if key in self._ttl and time.time() > self._ttl[key]:
            del self._store[key]
            del self._ttl[key]
            return None
        val = self._store.get(key)
        return str(val) if val is not None else None

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        self._store[key] = str(value) if not isinstance(value, str) else value
        if ex:
            self._ttl[key] = time.time() + ex
        elif key in self._ttl:
            del self._ttl[key]
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                count += 1
            if k in self._ttl:
                del self._ttl[k]
        return count

    def keys(self, pattern: str = "*") -> List[str]:
        prefix = pattern.replace("*", "")
        return [k for k in self._store.keys() if k.startswith(prefix)]

    def ping(self) -> bool:
        return True


class RedisClientManager:
    """Production Redis manager with connection pooling and standalone fallback."""

    def __init__(self, url: Optional[str] = None):
        self._url = url or redis_config.url
        self._client = None
        self._is_fallback = False
        self._connect()

    def _connect(self) -> None:
        if HAS_REDIS and redis is not None:
            try:
                client = redis.Redis.from_url(
                    self._url,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                )
                client.ping()
                self._client = client
                self._is_fallback = False
                logger.info(f"Connected to Redis at {self._url}")
                return
            except Exception as exc:
                logger.warning(f"Could not connect to Redis ({exc}). Initializing in-memory fallback cache.")
        
        self._client = InMemoryCacheFallback()
        self._is_fallback = True

    def get_client(self):
        return self._client

    @property
    def is_fallback(self) -> bool:
        return self._is_fallback

    def health_check(self) -> bool:
        try:
            return bool(self._client.ping())
        except Exception:
            return False


# Global Redis Manager instance
redis_manager = RedisClientManager()
