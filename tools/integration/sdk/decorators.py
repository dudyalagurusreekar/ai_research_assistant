"""Helper decorators for Sprint 12 Universal Connector SDK."""

import functools
import time
from typing import Callable, Any
from infrastructure.logging.logger import StructuredLogger

_logger = StructuredLogger("ConnectorDecorators")


def connector(name: str, protocol: str = "rest", description: str = ""):
    """Class decorator tagging a connector implementation with metadata."""
    def decorator(cls):
        cls._connector_name = name
        cls._connector_protocol = protocol
        cls._connector_description = description
        return cls
    return decorator


def rate_limited(calls_per_minute: int = 60):
    """Method decorator enforcing rate limiting per minute."""
    timestamps = []

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            nonlocal timestamps
            timestamps = [t for t in timestamps if now - t < 60.0]
            if len(timestamps) >= calls_per_minute:
                _logger.warning(f"Rate limit of {calls_per_minute}/min exceeded in decorator.")
                raise RuntimeError(f"Rate limit of {calls_per_minute}/min exceeded.")
            timestamps.append(now)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def audit_logged(action_name: str = ""):
    """Method decorator logging connector execution attempts and results."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            act = action_name or func.__name__
            conn_name = getattr(self, "connector_name", "unknown_connector")
            _logger.info(f"AUDIT EXECUTE: [{conn_name}] action={act}")
            start = time.time()
            try:
                res = await func(self, *args, **kwargs)
                elapsed = (time.time() - start) * 1000.0
                _logger.info(f"AUDIT SUCCESS: [{conn_name}] action={act} time={elapsed:.2f}ms")
                return res
            except Exception as e:
                elapsed = (time.time() - start) * 1000.0
                _logger.error(f"AUDIT FAILURE: [{conn_name}] action={act} time={elapsed:.2f}ms error={e}")
                raise
        return wrapper
    return decorator


def cacheable(ttl_seconds: int = 300):
    """Method decorator caching asynchronous return values."""
    cache_store = {}

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            now = time.time()
            if key in cache_store:
                cached_time, val = cache_store[key]
                if now - cached_time < ttl_seconds:
                    return val
            res = await func(self, *args, **kwargs)
            cache_store[key] = (now, res)
            return res
        return wrapper
    return decorator
