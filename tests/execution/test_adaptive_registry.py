"""Tests for AdaptiveToolRegistry and ToolCapabilityDescriptor."""

import pytest
from core.execution.models.descriptor import ToolCapabilityDescriptor, ToolHealthStatus
from core.execution.registry import AdaptiveToolRegistry, DEFAULT_DESCRIPTORS


class TestToolCapabilityDescriptor:
    def test_default_descriptor(self):
        desc = ToolCapabilityDescriptor(name="test_tool")
        assert desc.name == "test_tool"
        assert desc.reliability_score == 0.95
        assert desc.health_status == ToolHealthStatus.HEALTHY
        assert desc.is_available() is True

    def test_record_success_updates_metrics(self):
        desc = ToolCapabilityDescriptor(name="test_tool", reliability_score=0.90)
        desc.record_success(latency_ms=500.0)
        assert desc.total_calls == 1
        assert desc.successful_calls == 1
        assert desc.consecutive_failures == 0
        assert desc.reliability_score > 0.90

    def test_record_failure_degrades_health(self):
        desc = ToolCapabilityDescriptor(name="test_tool", reliability_score=0.90)
        desc.record_failure("error 1")
        assert desc.failed_calls == 1
        assert desc.consecutive_failures == 1
        assert desc.health_status == ToolHealthStatus.DEGRADED

        desc.record_failure("error 2")
        desc.record_failure("error 3")
        assert desc.consecutive_failures == 3
        assert desc.health_status == ToolHealthStatus.UNAVAILABLE
        assert desc.is_available() is False

    def test_compute_score_available(self):
        desc = ToolCapabilityDescriptor(name="test_tool", reliability_score=1.0)
        score = desc.compute_score()
        assert score > 0.5

    def test_compute_score_unavailable(self):
        desc = ToolCapabilityDescriptor(name="test_tool", health_status=ToolHealthStatus.UNAVAILABLE)
        score = desc.compute_score()
        assert score == 0.0

    def test_to_dict(self):
        desc = ToolCapabilityDescriptor(name="test_tool")
        d = desc.to_dict()
        assert d["name"] == "test_tool"
        assert "reliability_score" in d


class TestAdaptiveToolRegistry:
    def setup_method(self):
        self.registry = AdaptiveToolRegistry()

    def test_defaults_loaded(self):
        descriptors = self.registry.list_descriptors()
        assert len(descriptors) >= len(DEFAULT_DESCRIPTORS)
        names = {d.name for d in descriptors}
        assert "search_tool" in names
        assert "python_interpreter" in names

    def test_get_descriptor(self):
        desc = self.registry.get_descriptor("search_tool")
        assert desc is not None
        assert "search" in desc.capabilities

    def test_find_by_capability(self):
        matched = self.registry.find_by_capability("web_search")
        assert len(matched) >= 1
        assert any(d.name == "search_tool" for d in matched)

    def test_record_outcome_success(self):
        self.registry.record_outcome("search_tool", success=True, latency_ms=1200.0)
        desc = self.registry.get_descriptor("search_tool")
        assert desc.total_calls == 1

    def test_record_outcome_failure(self):
        self.registry.record_outcome("search_tool", success=False, error_message="timeout")
        desc = self.registry.get_descriptor("search_tool")
        assert desc.failed_calls == 1
        assert desc.health_status == ToolHealthStatus.DEGRADED

    def test_reset_health(self):
        self.registry.record_outcome("search_tool", success=False)
        self.registry.record_outcome("search_tool", success=False)
        self.registry.record_outcome("search_tool", success=False)
        assert self.registry.get_descriptor("search_tool").health_status == ToolHealthStatus.UNAVAILABLE

        self.registry.reset_health("search_tool")
        assert self.registry.get_descriptor("search_tool").health_status == ToolHealthStatus.HEALTHY
        assert self.registry.get_descriptor("search_tool").is_available() is True

    def test_register_from_tool_info(self):
        tool_info = {"name": "custom_tool", "description": "Custom cap", "capabilities": ["custom"]}
        desc = self.registry.register_from_tool_info(tool_info)
        assert desc.name == "custom_tool"
        assert self.registry.get_descriptor("custom_tool") is not None
