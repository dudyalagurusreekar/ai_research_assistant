"""Tests for GlobalRecoveryEngine."""
import asyncio
from core.orchestrator.recovery_engine import GlobalRecoveryEngine
from core.models.tool_result import ToolResult

def test_recovery_engine_success():
    async def _test():
        engine = GlobalRecoveryEngine(max_retries=2, base_backoff_ms=10)
        
        attempts = 0
        async def mock_func(parameters):
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise RuntimeError("Temporary failure")
            return ToolResult(tool_name="test_tool", success=True, data="recovered")

        result = await engine.execute_with_recovery("test_tool", mock_func, parameters={})
        assert result.success is True
        assert result.data == "recovered"
        assert result.metadata["retry_count"] == 1
        assert attempts == 2
    asyncio.run(_test())

def test_recovery_engine_exhaustion():
    async def _test():
        engine = GlobalRecoveryEngine(max_retries=2, base_backoff_ms=5)
        
        async def mock_func(parameters):
            raise ValueError("Persistent error")
            
        result = await engine.execute_with_recovery("test_tool", mock_func, parameters={})
        assert result.success is False
        assert result.metadata["degraded"] is True
        assert "Persistent error" in result.error_message
    asyncio.run(_test())
