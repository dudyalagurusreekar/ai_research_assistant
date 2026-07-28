"""Tests for UnifiedExecutionContext."""
import pytest
import asyncio
from core.utils.execution_context import UnifiedExecutionContext
from core.models.tool_result import ToolResult

def test_execution_context_success():
    async def _test():
        context = UnifiedExecutionContext(name="test_tool", session_id="session123")
        
        async def mock_func(parameters):
            await asyncio.sleep(0.01)
            return ToolResult(tool_name="test_tool", success=True, data="ok")
            
        result = await context.execute_async(mock_func, parameters={})
        assert result.success is True
        assert result.data == "ok"
        assert result.execution_time_ms >= 0
        assert "start_timestamp" in result.metadata
        assert "end_timestamp" in result.metadata
        assert result.metadata["retry_count"] == 0
    asyncio.run(_test())

def test_execution_context_exception():
    async def _test():
        context = UnifiedExecutionContext(name="test_tool")
        
        async def mock_func(parameters):
            raise ValueError("Something went wrong")
            
        with pytest.raises(ValueError):
            await context.execute_async(mock_func, parameters={})
    asyncio.run(_test())
