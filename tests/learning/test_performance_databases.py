"""Unit tests for ToolPerformanceDatabase and ProviderPerformanceDatabase."""

import tempfile
import shutil
import pytest
from core.learning.components.tool_performance_db import ToolPerformanceDatabase
from core.learning.components.provider_performance_db import ProviderPerformanceDatabase


@pytest.fixture
def temp_dbs():
    tmp_dir = tempfile.mkdtemp()
    tool_db = ToolPerformanceDatabase(storage_dir=tmp_dir)
    provider_db = ProviderPerformanceDatabase(storage_dir=tmp_dir)
    yield tool_db, provider_db
    shutil.rmtree(tmp_dir)


def test_tool_performance_db(temp_dbs):
    tool_db, _ = temp_dbs
    tool_db.record_tool_call("search_tool", success=True, latency_ms=120.0)
    tool_db.record_tool_call("search_tool", success=True, latency_ms=80.0)
    tool_db.record_tool_call("search_tool", success=False, latency_ms=500.0, error_type="503 Timeout")

    m = tool_db.get_tool_metrics("search_tool")
    assert m.total_calls == 3
    assert m.successful_calls == 2
    assert m.failed_calls == 1
    assert round(m.reliability_score, 2) == 0.67

    ranked = tool_db.rank_tools(["search_tool", "code_tool"])
    assert "search_tool" in ranked


def test_provider_performance_db(temp_dbs):
    _, provider_db = temp_dbs
    pid = "gemini/gemini-2.5-flash"
    provider_db.record_request(pid, success=True, latency_ms=250.0, tokens=150, cost_usd=0.0001)
    provider_db.record_request(pid, success=False, latency_ms=100.0, is_rate_limit=True)

    m = provider_db.get_provider_metrics(pid)
    assert m.total_requests == 2
    assert m.rate_limit_count == 1
    assert m.reliability_score == 0.5
