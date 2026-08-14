import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import time
from infrastructure.cache.cache_manager import CacheManager
from infrastructure.cache.redis_client import InMemoryCacheFallback, RedisClientManager


def test_redis_in_memory_fallback():
    manager = RedisClientManager(url="redis://non_existent_host:9999/0")
    client = manager.get_client()

    assert client.set("key1", "val1") is True
    assert client.get("key1") == "val1"
    assert client.delete("key1") == 1
    assert client.get("key1") is None


def test_cache_manager_operations():
    fallback_client = RedisClientManager(url="redis://non_existent_host:9999/0")
    cm = CacheManager(client_manager=fallback_client)

    # General KV
    cm.set("test_key", {"data": 123}, ttl_seconds=60)
    val = cm.get("test_key")
    assert val == {"data": 123}

    # Session Management
    cm.store_session("token_abc", {"user_id": "usr-1", "email": "a@b.com"})
    session = cm.get_session("token_abc")
    assert session["user_id"] == "usr-1"

    cm.revoke_session("token_abc")
    assert cm.get_session("token_abc") is None

    # Planner Caches
    cm.cache_planner_dag("plan-1", {"nodes": ["n1", "n2"]})
    dag = cm.get_planner_dag("plan-1")
    assert dag["nodes"] == ["n1", "n2"]

    # Browser Session State
    cm.store_browser_state("b-sess-1", {"url": "https://example.com"})
    state = cm.get_browser_state("b-sess-1")
    assert state["url"] == "https://example.com"

    # Workflow State
    cm.set_workflow_state("wf-1", {"status": "completed"})
    wf = cm.get_workflow_state("wf-1")
    assert wf["status"] == "completed"


def test_rate_limiter_sliding_window():
    fallback_client = RedisClientManager(url="redis://non_existent_host:9999/0")
    cm = CacheManager(client_manager=fallback_client)

    user_id = "user_rate_test"
    
    # Allow max 3 requests per 10 seconds
    for _ in range(3):
        assert cm.check_rate_limit(user_id, max_requests=3, window_seconds=10) is True

    # 4th request within window must be rejected
    assert cm.check_rate_limit(user_id, max_requests=3, window_seconds=10) is False
