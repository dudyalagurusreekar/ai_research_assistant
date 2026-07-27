"""Sandboxed Execution Engine for controlled code and command execution."""

import sys
import time
import asyncio
import subprocess
import tempfile
from tools.code.interfaces.code_interfaces import ISandboxedExecutionEngine
from tools.code.models.code_models import ExecutionResult
from infrastructure.logging.logger import StructuredLogger


class SandboxedExecutionEngine(ISandboxedExecutionEngine):
    """Executes code snippets in a controlled subprocess with timeout protection and output capture."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("SandboxedExecutionEngine")

    async def execute_code(self, code: str, language: str = "python", timeout_seconds: float = 10.0) -> ExecutionResult:
        """Run code snippet in secure process wrapper."""
        start_time = time.time()
        self._logger.info(f"Executing sandboxed {language} code snippet (timeout={timeout_seconds}s)")

        if language.lower() not in ["python", "py"]:
            return ExecutionResult(
                status="error",
                exit_code=1,
                stderr=f"Unsupported sandbox execution language '{language}'. Only 'python' is supported.",
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                tmp_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds,
            )
            exec_time_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                status="success" if proc.returncode == 0 else "error",
                exit_code=proc.returncode or 0,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
                execution_time_ms=round(exec_time_ms, 2),
            )

        except asyncio.TimeoutError:
            self._logger.warning(f"Sandboxed execution timed out after {timeout_seconds}s.")
            return ExecutionResult(
                status="timeout",
                exit_code=-1,
                stderr=f"Execution timed out after {timeout_seconds} seconds.",
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )
        except Exception as e:
            self._logger.error(f"Sandboxed execution failed: {e}")
            return ExecutionResult(
                status="error",
                exit_code=1,
                stderr=str(e),
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )
